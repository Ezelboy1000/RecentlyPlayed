# RecentlyPlayed
Python script to keep track of your recently played tracks on Spotify!

What it does or doesn't do:
- Creates/searches a playlist called "RecentlyPlayed"
- Doesn't create duplicate songs in your playlist
- Configurable polling interval (5 seconds is default)
- Can fill initial playlist with configurable amount of recent songs that Spotify kept track of (might contain duplicates though, off by default)
- Option to keep a max amount of songs in the playlist (50 is default)
- Option to move tracks back to top when played again (on by default)

What you'll need:
- Python 3
- A Spotify Account
- A new app on the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/login)

How to use:
- Edit the config section in RecentlyPlayed.py
- pip install -r requirements.txt
- python RecentlyPlayed.py
