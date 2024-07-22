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
SPOTIPY_CLIENT_ID = 'SPOTIPY_CLIENT_ID'
SPOTIPY_CLIENT_SECRET = 'SPOTIPY_CLIENT_SECRET'
SPOTIPY_REDIRECT_URI = 'http://localhost:8888/callback'
scope = "user-modify-playback-state user-read-playback-state"


class SpotifyApp:
    def __init__(self, root):
        self.root = root
        self.sp = None
        self.test_device_id = None
        self.test_window = None
        self.urls = self.init_urls()
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
        change_times_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        for i, (day, data) in enumerate(self.urls.items()):
            ttk.Label(change_times_frame, text=day).grid(column=0, row=i, sticky=tk.W)
            ttk.Label(change_times_frame, text="Recess:").grid(column=1, row=i, sticky=tk.W)
            ttk.Entry(change_times_frame, textvariable=data['time'], width=10).grid(column=2, row=i, sticky=tk.W)
            ttk.Label(change_times_frame, text="Lunch:").grid(column=3, row=i, sticky=tk.W)
            ttk.Entry(change_times_frame, textvariable=data['lunch_time'], width=10).grid(column=4, row=i, sticky=tk.W)

        ttk.Button(change_times_frame, text="Save Times", command=save_times).grid(column=0, row=len(self.urls), columnspan=5)

    def create_test_window(self):
        self.test_window = tk.Toplevel(self.root)
        self.test_window.title("Test Section")
        self.test_window.attributes("-topmost", True)
        test_frame = ttk.Frame(self.test_window, padding="10 10 10 10")
        test_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.test_url_entry = ttk.Entry(test_frame, width=50)
        self.test_url_entry.grid(column=0, row=0, sticky=(tk.W, tk.E))
        self.test_url_entry.insert(0, "Enter Spotify URL for testing...")

        test_buttons_frame = ttk.Frame(test_frame)
        test_buttons_frame.grid(column=0, row=1, sticky=(tk.W, tk.E))
        ttk.Button(test_buttons_frame, text="Play Test Song", command=self.play_test_song).grid(column=0, row=0)
        ttk.Button(test_buttons_frame, text="Stop Test Song", command=self.stop_test_song).grid(column=1, row=0)

    def init_urls(self):
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        urls = {}
        for day in days:
            urls[day] = {
                'url': tk.StringVar(),
                'time': tk.StringVar(value="11:25"),
                'lunch_time': tk.StringVar(value="14:10"),
                'label': ttk.Label(self.root, text=f"{day} Song:"),
                'time_display': ttk.Label(self.root, text="Recess: 11:25"),
                'lunch_time_display': ttk.Label(self.root, text="Lunch: 14:10"),
                'loop': tk.BooleanVar(value=True)  # Set loop to True by default
            }
        return urls

    def create_ui(self):
        self.root.title("Spotify Scheduler")
        main_frame = ttk.Frame(self.root, padding="10 10 10 10")
        main_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        for i, (day, data) in enumerate(self.urls.items()):
            ttk.Label(main_frame, text=day).grid(column=0, row=i, sticky=tk.W)
            ttk.Entry(main_frame, textvariable=data['url'], width=50).grid(column=1, row=i, sticky=(tk.W, tk.E))
            ttk.Label(main_frame, textvariable=data['url']).grid(column=2, row=i, sticky=(tk.W, tk.E))
            ttk.Checkbutton(main_frame, text="Loop", variable=data['loop']).grid(column=3, row=i, sticky=tk.W)
            data['label'].grid(column=0, row=i + len(self.urls), sticky=(tk.W, tk.E))
            data['time_display'].grid(column=1, row=i + len(self.urls), sticky=(tk.W, tk.E))
            data['lunch_time_display'].grid(column=2, row=i + len(self.urls), sticky=(tk.W, tk.E))

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(column=0, row=len(self.urls) * 2, columnspan=4, pady=10)
        ttk.Button(button_frame, text="Save URLs", command=self.save_urls).grid(column=0, row=0, padx=5)
        ttk.Button(button_frame, text="Change Music Times", command=self.change_music_times).grid(column=1, row=0, padx=5)
        ttk.Button(button_frame, text="Toggle Test Section", command=self.toggle_test_section).grid(column=2, row=0, padx=5)

        self.clock_label = ttk.Label(main_frame, text="")
        self.clock_label.grid(column=0, row=len(self.urls) * 2 + 1, columnspan=4)


if __name__ == "__main__":
    root = ThemedTk(theme="radiance")
    app = SpotifyApp(root)
    root.mainloop()
