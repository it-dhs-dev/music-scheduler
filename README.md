# Spotify Music Scheduler

This Python script provides a graphical user interface (GUI) to schedule Spotify music playback as a signal for students. It allows users to specify Spotify track URLs for each day of the week, which will be played on a loop at specific times (11:20 AM and 2:10 PM) for a duration of 5 minutes. The script also includes an option for testing song playback.

## Features

- **Schedule Songs**: Specify different Spotify track URLs for each day of the week.
- **Loop Playback**: Option to play songs on a loop.
- **Timed Playback**: Automatically play songs at 11:20 AM and 2:10 PM for 5 minutes.
- **Test Song Playback**: Play a song immediately for testing purposes.
- **User-Friendly GUI**: Easy-to-use interface with theme support.

## Installation

To set up and run the Spotify Music Scheduler, follow these steps:

1. **Clone the Repository**:
   ```sh
   git clone https://github.com/it-dhs-dev/music-scheduler.git
   cd music-scheduler

## Install Required Python Modules:
Run the provided script to install necessary Python modules:

    python install_packages.py

Alternatively, you can manually install the required modules:

    pip install spotipy ttkthemes

## Configure Spotify Credentials:
To get your Spotify Client ID and Client Secret, you'll need to create a Spotify Developer account and register a new application. Here are the steps to do that:

1. Sign up for Spotify Developer:

- Go to the Spotify Developer Dashboard.
- Log in with your Spotify account. If you don't have one, you'll need to create it.
- Create a New Application:

2. Once you're logged in, click on the "Create an App" button.
- Fill in the required details for your application (e.g., name, description, etc.).
- After filling in the details, click on "Create".
- Retrieve Client ID and Client Secret:

3. After creating the application, you'll be redirected to the application dashboard.
- Here, you can see your Client ID and Client Secret. You'll need to click on "Show Client Secret" to reveal it.
- Set Redirect URI:

4. In the application dashboard, find the "Edit Settings" button and click on it.
- In the "Redirect URIs" field, add http://localhost:8888/callback or any other URI you plan to use for redirecting after authentication.
- Click on "Save" to save your settings.

## Usage
Run the Script:

    python music_scheduler.py

GUI Instructions:
- Clock: Displays the current date and time.
- Daily Song URLs: Enter Spotify track URLs for each day of the week.
- Loop Option: Check to enable looping of the track.
- Save URLs and Start Schedule: Save the entered URLs and start the scheduler.
- Test Song: Enter a Spotify track URL and click "Play Test Song" to test playback. Click "Stop Test Song" to stop the test playback.
