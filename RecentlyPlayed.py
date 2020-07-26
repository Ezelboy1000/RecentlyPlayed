import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
import threading
import time

### CONFIG ###

username = 'CHANGE_ME' # Your spotify username, double check this on the spotify website
client_id = 'CHANGE_ME' # App client id (create an app on https://developer.spotify.com/dashboard/login)
client_secret = 'CHANGE_ME' # App client secret
redirect_uri = 'http://localhost:8080' # App redirect url

refresh_interval = 5 # Seconds to wait inbetween checking if a new song is playing
add_delay = 30 # Seconds to wait before adding a song to the playlist
prefill = False # Pulls recent songs from Spotify when creating a playlist (has duplicates)
fill_size = 50 # Amount of tracks to pull when prefilling, MAX 50
clean = True # Removes songs when playlist gets above playlist_size
playlist_size = 50 # Max size of playlist
move_playing = True # Moves the song back to the top of the playlist when playing it again
move_playing_playlist = False # Moves the song back the the top when playing the RecentlyPlayed playlist

##############

scope = 'user-read-currently-playing,user-read-recently-played,playlist-read-private,playlist-modify-private,playlist-modify-public'
token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)
spotify = spotipy.Spotify(auth=token)
playing_recently_played_playlist = False
recently_played_id = ''
playing_track_id = ''
playing = False

def login():
  global token
  global spotify
  # Updates the login
  token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)
  spotify = spotipy.Spotify(auth=token)

def checkplaylist():
  global recently_played_id
  # Gets all users playlists
  playlists = spotify.current_user_playlists(limit=50, offset=0)
  # Search for a playlist named RecentlyPlayed, if there is one use that
  for playlist in playlists['items']:
    if playlist['name'] == 'RecentlyPlayed':
      recently_played_id = playlist['id']

  # If there is no playlist called RecentlyPlayed, make one and fill it with tracks
  if recently_played_id == '':
    create = spotify.user_playlist_create(username, 'RecentlyPlayed', public=False, description='Made with: https://github.com/Ezelboy1000/RecentlyPlayed')
    recently_played_id = create['id']
    
    # If set will fill the playlist with recent tracks pulled from Spotify
    if prefill == True:
      RecentlyPlayedTracks = spotify.current_user_recently_played(limit=fill_size, after=None, before=None)
      addtracks = []
      for track in RecentlyPlayedTracks['items']:
        RecentlyPlayedTrack = track['track']['id']
        addtracks.append(RecentlyPlayedTrack)
      spotify.user_playlist_add_tracks(username, recently_played_id, addtracks)

def checkplaying():
  global playing
  playing = False
  # Checks if a song is playing, if not check again after set interval time
  while playing == False:
    try:
      check_playing = spotify.currently_playing(market=None)
      if check_playing['is_playing'] == True:
        if check_playing['currently_playing_type'] == 'track':
          playing = True
        else:
          time.sleep(refresh_interval)
      else:
        time.sleep(refresh_interval)
    except:
      # re-authenticate when token expires
      thread = threading.Thread(target=login)
      thread.start()
      thread.join()
      # sleep for our set time to not spam the API
      time.sleep(refresh_interval)

def checknewsong():
  global playing_track_id
  global playing_recently_played_playlist
  newtrack = 'no'
  # Keep looping till we find a new track
  while newtrack == 'no':
    # Waits specified amount of seconds before trying again
    time.sleep(refresh_interval)
    # Get current track from spotify
    current_track = spotify.current_user_playing_track()
    # If our new ID from spotify is different from the one we have saved, save this as the new track and stop loop
    if current_track['item']['id'] != playing_track_id:
      playing_track_id = current_track['item']['id']
      time.sleep(add_delay)
      current_track = spotify.current_user_playing_track()
      if current_track['item']['id'] == playing_track_id:
        newtrack = 'yes'
        # Check if we're playing the RecentlyPlayed playlist
        check_playing = spotify.currently_playing(market=None)
        if check_playing['context']['type'] == 'playlist':
          length1 = len(username) + 7 # Gets length to cut off the playlist uri (option 1)
          length2 = len(username) + 23 # Gets length to cut off the playlist uri (option 2)
          playing_playlist_id = check_playing['context']['uri'][length1:]
          playing_playlist_id_2 = check_playing['context']['uri'][length2:]
          if playing_playlist_id == recently_played_id:
            playing_recently_played_playlist = True
          elif playing_playlist_id_2 == recently_played_id:
            playing_recently_played_playlist = True
          else:
            playing_recently_played_playlist = False

def addsongtoplaylist():
  playlist = spotify.playlist(recently_played_id)
  alreadyinplaylist = 'no'
  # Check if the playing song is already in the playlist
  for track in playlist['tracks']['items']:
    if playing_track_id == track['track']['id']:
      alreadyinplaylist = 'yes'
  # Add to playlist if it's not in there already
  if alreadyinplaylist == 'no':
    addtrack = []
    addtrack.append(playing_track_id)
    spotify.user_playlist_add_tracks(username, recently_played_id, addtrack, position=0)
  # If enabled this will move the playing track to the top of the playlist
  if move_playing == True:
    if alreadyinplaylist == 'yes':
      if move_playing_playlist == False:
        if playing_recently_played_playlist == False:
          movetrack = []
          movetrack.append(playing_track_id)
          spotify.user_playlist_remove_all_occurrences_of_tracks(username, recently_played_id, movetrack)
          spotify.user_playlist_add_tracks(username, recently_played_id, movetrack, position=0)
      else:
          movetrack = []
          movetrack.append(playing_track_id)
          spotify.user_playlist_remove_all_occurrences_of_tracks(username, recently_played_id, movetrack)
          spotify.user_playlist_add_tracks(username, recently_played_id, movetrack, position=0)

def cleanplaylist():
  playlist = spotify.playlist(recently_played_id)
  # Checks if the playlist is over the playlist size, if it's over the set size it'll remove songs from the bottom of the playlist
  if playlist['tracks']['total'] > playlist_size:
    tracks = spotify.playlist_tracks(recently_played_id, fields=None, limit=50, offset=playlist_size, market=None)
    trackids = []
    for track in tracks['items']:
      trackid = track['track']['id']
      trackids.append(trackid)
    spotify.user_playlist_remove_all_occurrences_of_tracks(username, recently_played_id, trackids)

def main():
  # Start thread to find/create the RecentlyPlayed playlist
  thread = threading.Thread(target=checkplaylist)
  thread.start()
  thread.join()

  while True:
    try:
      # Start a thread to poll if user playing anything
      thread = threading.Thread(target=checkplaying)
      thread.start()
      thread.join()

      # Only do the other tasks if we're actually playing something
      if playing == True:
        # Start a thread to poll if a new song is playing
        thread = threading.Thread(target=checknewsong)
        thread.start()
        thread.join()

        # Start a thread to add the new song to the playlist (if it's not already on there)
        thread = threading.Thread(target=addsongtoplaylist)
        thread.start()
        thread.join()

        # Start a thread to clean the playlist (remove all songs on position over the playlist size)
        if clean == True:
          thread = threading.Thread(target=cleanplaylist)
          thread.start()
          thread.join()
    except:
      # re-authenticate when token expires
      thread = threading.Thread(target=login)
      thread.start()
      thread.join()

if __name__ == '__main__':
  # Start main
  main()
