import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime, timedelta
import threading
import time
from ttkthemes import ThemedTk

# Replace these with your Spotify app credentials
SPOTIPY_CLIENT_ID = '9975f0790eaf44d28d8844524b9e9cf5'
SPOTIPY_CLIENT_SECRET = 'fd86578b43f245df8cadee864b75e4b4'
SPOTIPY_REDIRECT_URI = 'http://localhost:8888/callback'

# Scope for playing a song
scope = "user-modify-playback-state user-read-playback-state"

# Initialize Spotify API client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope=scope))
# Function to play a song on loop for 5 minutes
def play_song_on_loop(track_id, loop):
    devices = sp.devices()
    if not devices['devices']:
        messagebox.showerror("Error", "No active devices found. Please open Spotify on a device and try again.")
        return
    device_id = devices['devices'][0]['id']
        # Calculate the end time (5 minutes from now)
    end_time = datetime.now() + timedelta(minutes=5)
    
    sp.start_playback(device_id=device_id, uris=[f'spotify:track:{track_id}'])
    if loop:
        sp.repeat('track', device_id=device_id)
    else:
        sp.repeat('off', device_id=device_id)
        # Continuously check if the current time has reached the end time
    while datetime.now() < end_time:
        time.sleep(1) # Sleep for 1 second to avoid busy-waiting
        # Pause the playback and turn off repeat mode
    sp.pause_playback(device_id=device_id)
    sp.repeat('off', device_id=device_id)

def schedule_song_playback(day, time_str, url, loop):
    def play_at_time():
        while True:
            now = datetime.now()
            scheduled_time = datetime.strptime(time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
            if now.strftime("%A") == day:
                if now > scheduled_time:
                    scheduled_time += timedelta(days=1)
                sleep_duration = (scheduled_time - now).total_seconds()
                time.sleep(sleep_duration)
                track_id = url.split("/")[-1].split("?")[0]
                play_song_on_loop(track_id, loop)
            else:
                time.sleep(3600)  # Check once every hour if it's the correct day

    threading.Thread(target=play_at_time, daemon=True).start()

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
        sp.repeat('track', device_id=test_device_id)  # Set repeat mode for test song
        messagebox.showinfo("Success", "Playing the test song!")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def stop_test_song():
    try:
        if test_device_id:
            sp.pause_playback(device_id=test_device_id)
            sp.repeat('off', device_id=test_device_id)  # Turn off repeat mode
            messagebox.showinfo("Success", "Test song stopped!")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def update_clock():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clock_label.config(text=now)
    root.after(1000, update_clock)

def get_song_name(url):
    track_id = url.split("/")[-1].split("?")[0]
    track_info = sp.track(track_id)
    return track_info['name']

def toggle_test_section():
    if test_frame.winfo_viewable():
        test_frame.pack_forget()
        toggle_button.config(text="Show Test Song URL")
    else:
        test_frame.pack()
        toggle_button.config(text="Hide Test Song URL")

# Create the main application window
root = ThemedTk(theme="scidpurple")
root.title("Spotify Song Player")

# Add a clock at the top
clock_frame = tk.Frame(root)
clock_frame.pack(pady=10)
clock_label = tk.Label(clock_frame, font=("Helvetica", 16))
clock_label.pack()
update_clock()

# Create a frame for the daily song URLs
daily_frame = ttk.Frame(root, padding="10 10 10 10")
daily_frame.pack(pady=10, fill=tk.X, padx=10)

daily_label = ttk.Label(daily_frame, text="Daily Song URLs", font=("Helvetica", 14, "bold"))
daily_label.grid(row=0, column=0, columnspan=3, pady=10)

# Dictionary to store the URLs for each day and their labels and loop settings
urls = {
    'Monday': {'url': tk.StringVar(), 'label': None, 'loop': tk.BooleanVar(value=True)},
    'Tuesday': {'url': tk.StringVar(), 'label': None, 'loop': tk.BooleanVar(value=True)},
    'Wednesday': {'url': tk.StringVar(), 'label': None, 'loop': tk.BooleanVar(value=True)},
    'Thursday': {'url': tk.StringVar(), 'label': None, 'loop': tk.BooleanVar(value=True)},
    'Friday': {'url': tk.StringVar(), 'label': None, 'loop': tk.BooleanVar(value=True)}
}

def save_urls():
    for day, data in urls.items():
        url = data['url'].get()
        if url:
            song_name = get_song_name(url)
            data['label'].config(text=f"{day} Song: {song_name}")
                        # Schedule the song playback at 11:25 AM and 2:10 PM
            schedule_song_playback(day, "11:20", url, data['loop'].get())
            schedule_song_playback(day, "14:10", url, data['loop'].get())
    messagebox.showinfo("Success", "URLs saved and schedules set!")

# Create and place the widgets for daily song URLs
row_counter = 1
for day, data in urls.items():
    day_frame = ttk.Frame(daily_frame)
    day_frame.grid(row=row_counter, column=0, columnspan=3, pady=5, sticky='w')

    label = ttk.Label(day_frame, text=f"{day}:")
    label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
    
    entry = ttk.Entry(day_frame, textvariable=data['url'], width=50)
    entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
    entry.insert(0, data['url'].get())
    
    loop_check = ttk.Checkbutton(day_frame, text="Loop", variable=data['loop'])
    loop_check.grid(row=0, column=2, padx=5, pady=5, sticky='w')
    
    data['label'] = ttk.Label(day_frame, text=f"{day} Song: Not Set", font=("Helvetica", 10))
    data['label'].grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky='w')

    row_counter += 1

# Button to toggle the Test Song URL section
toggle_button = ttk.Button(root, text="Show Test Song URL", command=toggle_test_section)
toggle_button.pack(pady=10)

# Field for testing URL
test_frame = ttk.Frame(root, padding="10 10 10 10")

test_label = ttk.Label(test_frame, text="Test Song URL", font=("Helvetica", 14, "bold"))
test_label.grid(row=0, column=0, columnspan=2, pady=10)

ttk.Label(test_frame, text="Enter Spotify URL for Testing:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
test_url_entry = ttk.Entry(test_frame, width=50)
test_url_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')

play_button = ttk.Button(test_frame, text="Play Test Song", command=play_test_song)
play_button.grid(row=2, column=0, padx=5, pady=5, sticky='w')

stop_button = ttk.Button(test_frame, text="Stop Test Song", command=stop_test_song)
stop_button.grid(row=2, column=1, padx=5, pady=5, sticky='w')

# Initially hide the Test Song URL section
test_frame.pack_forget()

# Save URLs button
save_button = ttk.Button(root, text="Save URLs and Start Schedule", command=save_urls)
save_button.pack(pady=10)

root.mainloop()
