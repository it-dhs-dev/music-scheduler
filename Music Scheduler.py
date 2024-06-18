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

# Function to perform Spotify authentication
def authenticate_spotify():
    try:
        auth_manager = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                    client_secret=SPOTIPY_CLIENT_SECRET,
                                    redirect_uri=SPOTIPY_REDIRECT_URI,
                                    scope=scope)
        global sp
        sp = spotipy.Spotify(auth_manager=auth_manager)
        logging.info("Successfully authenticated with Spotify!")
    except Exception as e:
        logging.error(f"Error in Spotify authentication: {e}")
        messagebox.showerror("Authentication Error", "Failed to authenticate with Spotify. Please check your credentials.")

authenticate_spotify()

# Function to play a song on loop for a specified duration
def play_song_on_loop(track_id, loop):
    try:
        devices = sp.devices()
        if not devices['devices']:
            messagebox.showerror("Error", "No active devices found. Please open Spotify on a device and try again.")
            return
        device_id = devices['devices'][0]['id']
        end_time = datetime.now() + timedelta(minutes=5)
        sp.start_playback(device_id=device_id, uris=[f'spotify:track:{track_id}'])
        sp.repeat('track' if loop else 'off', device_id=device_id)
        while datetime.now() < end_time:
            time.sleep(1)
        sp.pause_playback(device_id=device_id)
        sp.repeat('off', device_id=device_id)
    except Exception as e:
        logging.error(f"Error in play_song_on_loop: {e}")
        messagebox.showerror("Error", str(e))

# Function to schedule song playback on a specific day and time
def schedule_song_playback(day, time_str, url, loop):
    def play_at_time():
        try:
            while True:
                now = datetime.now()
                scheduled_time = datetime.strptime(time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
                days_ahead = (list(calendar.day_name).index(day) - now.weekday() + 7) % 7
                if days_ahead == 0 and now > scheduled_time:
                    days_ahead += 7
                scheduled_time += timedelta(days=days_ahead)
                sleep_duration = (scheduled_time - now).total_seconds()
                logging.info(f"Scheduled to play at {scheduled_time}, sleeping for {sleep_duration} seconds")
                time.sleep(sleep_duration)
                track_id = url.split("/")[-1].split("?")[0]
                play_song_on_loop(track_id, loop)
        except Exception as e:
            logging.error(f"Error in play_at_time thread: {e}")

    threading.Thread(target=play_at_time, daemon=True).start()

# Function to play a test song
def play_test_song():
    url = test_url_entry.get()
    try:
        track_id = url.split("/")[-1].split("?")[0]
        devices = sp.devices()
        if not devices['devices']:
            messagebox.showerror("Error", "No active devices found. Please open Spotify on a device and try again.")
            return
        global test_device_id
        test_device_id = devices['devices'][0]['id']
        sp.start_playback(device_id=test_device_id, uris=[f'spotify:track:{track_id}'])
        sp.repeat('track', device_id=test_device_id)
        messagebox.showinfo("Success", "Playing the test song!")
    except Exception as e:
        logging.error(f"Error in play_test_song: {e}")
        messagebox.showerror("Error", str(e))

# Function to stop the test song
def stop_test_song():
    try:
        if test_device_id:
            sp.pause_playback(device_id=test_device_id)
            sp.repeat('off', device_id=test_device_id)
            messagebox.showinfo("Success", "Test song stopped!")
    except Exception as e:
        logging.error(f"Error in stop_test_song: {e}")
        messagebox.showerror("Error", str(e))

# Function to update the clock display
def update_clock():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clock_label.config(text=now)
    root.after(1000, update_clock)

# Function to validate a URL asynchronously
def validate_url_async(url, day):
    def validate_url():
        try:
            track_id = url.split("/")[-1].split("?")[0]
            track_info = sp.track(track_id)
            song_name = track_info['name']
        except Exception as e:
            logging.error(f"Error validating URL: {e}")
            song_name = "Invalid URL"
        
        def update_label():
            urls[day]['label'].config(text=f"{day} Song: {song_name}")

        root.after(0, update_label)

    threading.Thread(target=validate_url).start()

# Function to save the URLs and schedule playback
def save_urls():
    url_data = {day: data['url'].get() for day, data in urls.items()}
    with open("urls.json", "w") as file:
        json.dump(url_data, file)
    for day, data in urls.items():
        url = data['url'].get()
        if url:
            validate_url_async(url, day)
            logging.info(f"Scheduling {day} at {data['time'].get()} and {data['lunch_time'].get()}")
            schedule_song_playback(day, data['time'].get(), url, data['loop'].get())
            schedule_song_playback(day, data['lunch_time'].get(), url, data['loop'].get())
    messagebox.showinfo("Success", "URLs saved and schedules set!")

# Function to load saved URLs
def load_urls():
    if os.path.exists("urls.json"):
        with open("urls.json", "r") as file:
            url_data = json.load(file)
        for day, url in url_data.items():
            if day in urls:
                urls[day]['url'].set(url)
                validate_url_async(url, day)

# Function to toggle the test section
def toggle_test_section():
    global test_window
    if test_window is None or not test_window.winfo_exists():
        create_test_window()
    else:
        test_window.lift()

# Function to change the music times
def change_music_times():
    def save_times():
        for day, data in urls.items():
            data['time_display'].config(text=f"Recess: {data['time'].get()}")
            data['lunch_time_display'].config(text=f"Lunch: {data['lunch_time'].get()}")
            url = data['url'].get()
            if url:
                schedule_song_playback(day, data['time'].get(), url, data['loop'].get())
                schedule_song_playback(day, data['lunch_time'].get(), url, data['loop'].get())
        messagebox.showinfo("Success", "Times saved and schedules set!")
        change_times_window.destroy()

    change_times_window = tk.Toplevel(root)
    change_times_window.title("Change Music Times")
    change_times_window.attributes("-topmost", True)
    change_times_frame = ttk.Frame(change_times_window, padding="10 10 10 10")
    change_times_frame.pack()
    ttk.Label(change_times_frame, text="Change Music Times", font=("Helvetica", 14, "bold")).grid(row=0, column=0, columnspan=3, pady=10)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    for i, day in enumerate(days):
        ttk.Label(change_times_frame, text=day).grid(row=i+1, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(change_times_frame, text="Recess:").grid(row=i+1, column=1, padx=5, pady=5, sticky='w')
        ttk.Entry(change_times_frame, textvariable=urls[day]['time'], width=10).grid(row=i+1, column=2, padx=5, pady=5, sticky='w')
        ttk.Label(change_times_frame, text="Lunch:").grid(row=i+1, column=3, padx=5, pady=5, sticky='w')
        ttk.Entry(change_times_frame, textvariable=urls[day]['lunch_time'], width=10).grid(row=i+1, column=4, padx=5, pady=5, sticky='w')
    ttk.Button(change_times_frame, text="Save Times", command=save_times).grid(row=len(days)+1, column=0, columnspan=5, pady=10)

# Function to create the test window
def create_test_window():
    global test_window
    test_window = tk.Toplevel(root)
    test_window.title("Test Song Player")
    test_window.attributes("-topmost", True)
    test_frame = ttk.Frame(test_window, padding="10 10 10 10")
    test_frame.pack()
    ttk.Label(test_frame, text="Enter Spotify URL for Test Song:", font=("Helvetica", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
    global test_url_entry
    test_url_entry = ttk.Entry(test_frame, width=50)
    test_url_entry.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky='w')
    ttk.Button(test_frame, text="Play Test Song", command=play_test_song).grid(row=2, column=0, padx=5, pady=5, sticky='w')
    ttk.Button(test_frame, text="Stop Test Song", command=stop_test_song).grid(row=2, column=1, padx=5, pady=5, sticky='w')

root = ThemedTk(theme="scidpurple")
root.title("Spotify Song Player")

# Initialize test_window as None
test_window = None

# Clock display
clock_frame = tk.Frame(root)
clock_frame.pack(pady=10)
clock_label = tk.Label(clock_frame, font=("Helvetica", 16))
clock_label.pack()
update_clock()

# Daily song URLs frame
daily_frame = ttk.Frame(root, padding="10 10 10 10")
daily_frame.pack(pady=10, fill=tk.X, padx=10)
daily_label = ttk.Label(daily_frame, text="Daily Song URLs", font=("Helvetica", 14, "bold"))
daily_label.grid(row=0, column=0, columnspan=3, pady=10)

urls = {
    'Monday': {'url': tk.StringVar(), 'label': None, 'loop': tk.BooleanVar(value=True), 'time': tk.StringVar(value='11:25'), 'lunch_time': tk.StringVar(value='14:10'), 'time_display': None, 'lunch_time_display': None},
    'Tuesday': {'url': tk.StringVar(), 'label': None, 'loop': tk.BooleanVar(value=True), 'time': tk.StringVar(value='11:25'), 'lunch_time': tk.StringVar(value='14:10'), 'time_display': None, 'lunch_time_display': None},
    'Wednesday': {'url': tk.StringVar(), 'label': None, 'loop': tk.BooleanVar(value=True), 'time': tk.StringVar(value='11:25'), 'lunch_time': tk.StringVar(value='14:10'), 'time_display': None, 'lunch_time_display': None},
    'Thursday': {'url': tk.StringVar(), 'label': None, 'loop': tk.BooleanVar(value=True), 'time': tk.StringVar(value='11:25'), 'lunch_time': tk.StringVar(value='14:10'), 'time_display': None, 'lunch_time_display': None},
    'Friday': {'url': tk.StringVar(), 'label': None, 'loop': tk.BooleanVar(value=True), 'time': tk.StringVar(value='11:25'), 'lunch_time': tk.StringVar(value='14:10'), 'time_display': None, 'lunch_time_display': None}
}

row_counter = 1
for day, data in urls.items():
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
toggle_button = ttk.Button(daily_frame, text="Test Song", command=toggle_test_section)
toggle_button.grid(row=0, column=0, sticky="w", padx=10, pady=10)

save_button = ttk.Button(root, text="Save URLs and Start Schedule", command=save_urls)
save_button.pack(pady=10)

change_times_button = ttk.Button(daily_frame, text="Music Times", command=change_music_times)
change_times_button.grid(row=0, column=2, sticky="e", padx=10, pady=10)

# Load URLs when the script starts
load_urls()

root.mainloop()
