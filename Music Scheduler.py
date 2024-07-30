import tkinter as tk
from tkinter import messagebox, ttk
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime, timedelta
import threading
import time
from ttkthemes import ThemedTk
import os
import calendar
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Replace these with your Spotify app credentials
SPOTIPY_CLIENT_ID = 'your_spotify_client_id'
SPOTIPY_CLIENT_SECRET = 'your_spotify_client_secret'
SPOTIPY_REDIRECT_URI = 'http://localhost:8888/callback'
scope = "user-modify-playback-state user-read-playback-state"


class SpotifyApp:
    def __init__(self, root):
        self.root = root
        self.sp = None
        self.test_device_id = None
        self.test_window = None
        self.urls = self.init_urls()
        self.original_urls = {}
        self.unsaved_changes = False
        self.scheduled_threads = {}  # Dictionary to track scheduled threads and control events

        self.authenticate_spotify()
        self.create_ui()
        self.load_urls()
        self.update_clock()

    def authenticate_spotify(self):
        try:
            auth_manager = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                        client_secret=SPOTIPY_CLIENT_SECRET,
                                        redirect_uri=SPOTIPY_REDIRECT_URI,
                                        scope=scope)
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            logging.info("Successfully authenticated with Spotify!")
        except Exception as e:
            logging.error(f"Error in Spotify authentication: {e}")
            messagebox.showerror("Authentication Error", "Failed to authenticate with Spotify. Please check your credentials.")

    def play_song_on_loop(self, track_id, loop):
        try:
            devices = self.sp.devices()
            if not devices['devices']:
                messagebox.showerror("Error", "No active devices found. Please open Spotify on a device and try again.")
                return
            device_id = devices['devices'][0]['id']
            end_time = datetime.now() + timedelta(minutes=5)
            self.sp.start_playback(device_id=device_id, uris=[f'spotify:track:{track_id}'])
            self.sp.repeat('track' if loop else 'off', device_id=device_id)
            while datetime.now() < end_time:
                time.sleep(1)
            self.sp.pause_playback(device_id=device_id)
            self.sp.repeat('off', device_id=device_id)
        except Exception as e:
            logging.error(f"Error in play_song_on_loop: {e}")
            messagebox.showerror("Error", str(e))

    def schedule_song_playback(self, day, time_str, url, loop, period):
        # Use distinct keys for recess and lunch schedules
        schedule_key = f"{day}_{period}"
        
        # If there's an existing scheduled thread for the period, stop it
        if schedule_key in self.scheduled_threads:
            self.scheduled_threads[schedule_key]['event'].set()

        stop_event = threading.Event()
        self.scheduled_threads[schedule_key] = {
            'thread': threading.Thread(target=self.play_at_time, args=(day, time_str, url, loop, stop_event), daemon=True),
            'event': stop_event
        }
        self.scheduled_threads[schedule_key]['thread'].start()

    def play_at_time(self, day, time_str, url, loop, stop_event):
        try:
            while not stop_event.is_set():
                now = datetime.now()
                scheduled_time = datetime.strptime(time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
                days_ahead = (list(calendar.day_name).index(day) - now.weekday() + 7) % 7
                if days_ahead == 0 and now > scheduled_time:
                    days_ahead += 7
                scheduled_time += timedelta(days=days_ahead)
                sleep_duration = (scheduled_time - now).total_seconds()
                logging.info(f"Scheduled to play at {scheduled_time}, sleeping for {sleep_duration} seconds")

                # Wait for the scheduled time or until the stop event is set
                stop_event.wait(timeout=sleep_duration)
                if stop_event.is_set():
                    break

                track_id = url.split("/")[-1].split("?")[0]
                self.play_song_on_loop(track_id, loop)

                # After playing, wait for a week for the next play
                stop_event.wait(timeout=7 * 24 * 3600)
        except Exception as e:
            logging.error(f"Error in play_at_time thread: {e}")

    def play_test_song(self):
        url = self.test_url_entry.get()
        try:
            track_id = url.split("/")[-1].split("?")[0]
            devices = self.sp.devices()
            if not devices['devices']:
                messagebox.showerror("Error", "No active devices found. Please open Spotify on a device and try again.")
                return
            self.test_device_id = devices['devices'][0]['id']
            self.sp.start_playback(device_id=self.test_device_id, uris=[f'spotify:track:{track_id}'])
            self.sp.repeat('track', device_id=self.test_device_id)
            messagebox.showinfo("Success", "Playing the test song!")
        except Exception as e:
            logging.error(f"Error in play_test_song: {e}")
            messagebox.showerror("Error", str(e))

    def stop_test_song(self):
        try:
            if self.test_device_id:
                self.sp.pause_playback(device_id=self.test_device_id)
                self.sp.repeat('off', device_id=self.test_device_id)
                messagebox.showinfo("Success", "Test song stopped!")
        except Exception as e:
            logging.error(f"Error in stop_test_song: {e}")
            messagebox.showerror("Error", str(e))

    def update_clock(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.clock_label.config(text=now)
        self.root.after(1000, self.update_clock)

    def validate_url_async(self, url, day):
        def validate_url():
            try:
                track_id = url.split("/")[-1].split("?")[0]
                track_info = self.sp.track(track_id)
                song_name = track_info['name']
            except Exception as e:
                logging.error(f"Error validating URL: {e}")
                song_name = "Invalid URL"

            def update_label():
                self.urls[day]['label'].config(text=f"{day} Song: {song_name}")

            self.root.after(0, update_label)

        threading.Thread(target=validate_url).start()

    def save_urls(self):
        url_data = {day: data['url'].get() for day, data in self.urls.items()}
        with open("urls.json", "w") as file:
            json.dump(url_data, file)
        self.original_urls = url_data  # Save the current state as the original
        self.reset_unsaved_changes_status()
        for day, data in self.urls.items():
            url = data['url'].get()
            if url:
                self.validate_url_async(url, day)
                logging.info(f"Scheduling {day} at {data['time'].get()} and {data['lunch_time'].get()}")
                self.schedule_song_playback(day, data['time'].get(), url, data['loop'].get(), 'recess')
                self.schedule_song_playback(day, data['lunch_time'].get(), url, data['loop'].get(), 'lunch')
        messagebox.showinfo("Success", "URLs saved and schedules set!")

    def load_urls(self):
        if os.path.exists("urls.json"):
            with open("urls.json", "r") as file:
                url_data = json.load(file)
            for day, url in url_data.items():
                if day in self.urls:
                    self.urls[day]['url'].set(url)
                    self.original_urls[day] = url
                    self.validate_url_async(url, day)

    def toggle_test_section(self):
        if self.test_window is None or not self.test_window.winfo_exists():
            self.create_test_window()
        else:
            self.test_window.lift()

    def change_music_times(self):
        def save_times():
            for day, data in self.urls.items():
                data['time_display'].config(text=f"Recess: {data['time'].get()}")
                data['lunch_time_display'].config(text=f"Lunch: {data['lunch_time'].get()}")
                url = data['url'].get()
                if url:
                    self.schedule_song_playback(day, data['time'].get(), url, data['loop'].get(), 'recess')
                    self.schedule_song_playback(day, data['lunch_time'].get(), url, data['loop'].get(), 'lunch')
            messagebox.showinfo("Success", "Times saved and schedules set!")
            change_times_window.destroy()

        change_times_window = tk.Toplevel(self.root)
        change_times_window.title("Change Music Times")
        change_times_window.attributes("-topmost", True)
        change_times_frame = ttk.Frame(change_times_window, padding="10 10 10 10")
        change_times_frame.pack()
        ttk.Label(change_times_frame, text="Change Music Times", font=("Helvetica", 14, "bold")).grid(row=0, column=0, columnspan=3, pady=10)
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        for i, day in enumerate(days):
            ttk.Label(change_times_frame, text=day).grid(row=i + 1, column=0, padx=5, pady=5, sticky='w')
            ttk.Label(change_times_frame, text="Recess:").grid(row=i + 1, column=1, padx=5, pady=5, sticky='w')
            ttk.Entry(change_times_frame, textvariable=self.urls[day]['time'], width=10).grid(row=i + 1, column=2, padx=5, pady=5, sticky='w')
            ttk.Label(change_times_frame, text="Lunch:").grid(row=i + 1, column=3, padx=5, pady=5, sticky='w')
            ttk.Entry(change_times_frame, textvariable=self.urls[day]['lunch_time'], width=10).grid(row=i + 1, column=4, padx=5, pady=5, sticky='w')
        ttk.Button(change_times_frame, text="Save Times", command=save_times).grid(row=len(days) + 1, column=0, columnspan=5, pady=10)

    def create_test_window(self):
        self.test_window = tk.Toplevel(self.root)
        self.test_window.title("Test Song Player")
        self.test_window.attributes("-topmost", True)

        test_frame = ttk.Frame(self.test_window, padding="10 10 10 10")
        test_frame.pack()
        ttk.Label(test_frame, text="Enter Spotify URL for Test Song:", font=("Helvetica", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        self.test_url_entry = ttk.Entry(test_frame, width=50)
        self.test_url_entry.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky='w')
        ttk.Button(test_frame, text="Play Test Song", command=self.play_test_song).grid(row=2, column=0, padx=5, pady=5, sticky='w')
        ttk.Button(test_frame, text="Stop Test Song", command=self.stop_test_song).grid(row=2, column=1, padx=5, pady=5, sticky='w')

    def init_urls(self):
        return {
            'Monday': {'url': tk.StringVar(), 'label': None, 'loop': tk.BooleanVar(value=True), 'time': tk.StringVar(value='11:25'), 'lunch_time': tk.StringVar(value='14:10'), 'time_display': None, 'lunch_time_display': None},
            'Tuesday': {'url': tk.StringVar(), 'label': None, 'loop': tk.BooleanVar(value=True), 'time': tk.StringVar(value='11:25'), 'lunch_time': tk.StringVar(value='14:10'), 'time_display': None, 'lunch_time_display': None},
            'Wednesday': {'url': tk.StringVar(), 'label': None, 'loop': tk.BooleanVar(value=True), 'time': tk.StringVar(value='11:25'), 'lunch_time': tk.StringVar(value='14:10'), 'time_display': None, 'lunch_time_display': None},
            'Thursday': {'url': tk.StringVar(), 'label': None, 'loop': tk.BooleanVar(value=True), 'time': tk.StringVar(value='11:25'), 'lunch_time': tk.StringVar(value='14:10'), 'time_display': None, 'lunch_time_display': None},
            'Friday': {'url': tk.StringVar(), 'label': None, 'loop': tk.BooleanVar(value=True), 'time': tk.StringVar(value='11:25'), 'lunch_time': tk.StringVar(value='14:10'), 'time_display': None, 'lunch_time_display': None}
        }

    def create_ui(self):
        # Clock display
        clock_frame = tk.Frame(self.root)
        clock_frame.pack(pady=10)
        self.clock_label = tk.Label(clock_frame, font=("Helvetica", 16))
        self.clock_label.pack()
        
        # Daily song URLs frame
        daily_frame = ttk.Frame(self.root, padding="10 10 10 10")
        daily_frame.pack(pady=10, fill=tk.X, padx=10)
        daily_label = ttk.Label(daily_frame, text="Daily Song URLs", font=("Helvetica", 14, "bold"))
        daily_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        row_counter = 1
        for day, data in self.urls.items():
            day_frame = ttk.Frame(daily_frame)
            day_frame.grid(row=row_counter, column=0, columnspan=3, pady=5, sticky='w')
            ttk.Label(day_frame, text=f"{day}:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
            ttk.Entry(day_frame, textvariable=data['url'], width=50).grid(row=0, column=1, padx=5, pady=5, sticky='w')
            ttk.Checkbutton(day_frame, text="Loop", variable=data['loop']).grid(row=0, column=2, padx=5, pady=5, sticky='w')
            data['time_display'] = ttk.Label(day_frame, text=f"Recess: {data['time'].get()}")
            data['time_display'].grid(row=1, column=1, padx=5, pady=5, sticky='w')
            data['lunch_time_display'] = ttk.Label(day_frame, text=f"Lunch: {data['lunch_time'].get()}")
            data['lunch_time_display'].grid(row=1, column=2, padx=5, pady=5, sticky='w')
            data['label'] = ttk.Label(day_frame, text=f"{day} Song: Not Set", font=("Helvetica", 10))
            data['label'].grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky='w')
            row_counter += 1
        
        # Buttons
        toggle_button = ttk.Button(daily_frame, text="Test Song", command=self.toggle_test_section)
        toggle_button.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        save_button = ttk.Button(self.root, text="Save URLs and Start Schedule", command=self.save_urls)
        save_button.pack(pady=10)

        change_times_button = ttk.Button(daily_frame, text="Music Times", command=self.change_music_times)
        change_times_button.grid(row=0, column=2, sticky="e", padx=10, pady=10)


root = ThemedTk(theme="scidpurple")
root.title("Spotify Song Player")

app = SpotifyApp(root)

# Load URLs when the script starts
app.load_urls()

root.mainloop()
