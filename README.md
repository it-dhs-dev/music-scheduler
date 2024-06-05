Spotify Music Scheduler
This Python script provides a graphical user interface (GUI) to schedule Spotify music playback as a signal for students. It allows users to specify Spotify track URLs for each day of the week, which will be played on a loop at specific times (11:20 AM and 2:10 PM) for a duration of 5 minutes. The script also includes an option for testing song playback.

Features
Schedule Songs: Specify different Spotify track URLs for each day of the week.
Loop Playback: Option to play songs on a loop.
Timed Playback: Automatically play songs at 11:20 AM and 2:10 PM for 5 minutes.
Test Song Playback: Play a song immediately for testing purposes.
User-Friendly GUI: Easy-to-use interface with theme support.
Installation
To set up and run the Spotify Music Scheduler, follow these steps:

Clone the Repository:

sh
Copy code
git clone https://github.com/yourusername/spotify-music-scheduler.git
cd spotify-music-scheduler
Install Required Python Modules:
Run the provided script to install necessary Python modules:

sh
Copy code
python install_packages.py
Alternatively, you can manually install the required modules:

sh
Copy code
pip install spotipy ttkthemes
Configure Spotify Credentials:
Replace the placeholder values for SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, and SPOTIPY_REDIRECT_URI with your actual Spotify API credentials in the music_scheduler.py script.

Usage
Run the Script:

sh
Copy code
python music_scheduler.py
GUI Instructions:

Clock: Displays the current date and time.
Daily Song URLs: Enter Spotify track URLs for each day of the week.
Loop Option: Check to enable looping of the track.
Save URLs and Start Schedule: Save the entered URLs and start the scheduler.
Test Song: Enter a Spotify track URL and click "Play Test Song" to test playback. Click "Stop Test Song" to stop the test playback.
Example

Contributing
Contributions are welcome! Feel free to open issues or submit pull requests.

License
This project is licensed under the MIT License. See the LICENSE file for details.

Contact
For any questions or suggestions, please contact your-email@example.com.

Files
music_scheduler.py
The main script file that contains the GUI and scheduling logic.

install_packages.py
A script to install the required Python modules.

README.md
Documentation file with setup instructions and usage details.
