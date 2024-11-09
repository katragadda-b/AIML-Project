import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import random
import streamlit as st

st.set_page_config(
    page_title="Melody Match - Song Recommender",
    layout="centered",
    initial_sidebar_state="expanded"
)

SPOTIPY_CLIENT_ID = 'your_spotify_client_id'
SPOTIPY_CLIENT_SECRET = 'your_spotify_client_secret' #you can get these on spotify developer platform
SPOTIPY_REDIRECT_URI = "http://localhost:8888/callback"

scope = "playlist-modify-public user-library-read"
auth_manager = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI, scope=scope)
sp = spotipy.Spotify(auth_manager=auth_manager)

def get_artist_id(artist_name):
    try:
        results = sp.search(q=f"artist:{artist_name}", type='artist', limit=1)
        if results['artists']['items']:
            return results['artists']['items'][0]['id']
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching artist ID from Spotify: {e}")
        return None

def get_top_tracks(artist_id):
    try:
        top_tracks = sp.artist_top_tracks(artist_id, country='US')
        return [(track['name'], track['artists'][0]['name'], track['album']['name'], track['uri']) for track in top_tracks['tracks']]
    except Exception as e:
        st.error(f"Error fetching top tracks from Spotify: {e}")
        return []

def get_related_artist_tracks(artist_id):
    try:
        related_artists = sp.artist_related_artists(artist_id)['artists']
        related_tracks = []
        for artist in related_artists[:5]:  # Limit to 5 artists
            related_tracks.extend(get_top_tracks(artist['id']))
        return random.sample(related_tracks, min(5, len(related_tracks)))
    except Exception as e:
        st.error(f"Error fetching related artists from Spotify: {e}")
        return []

def get_genre(artist_id):
    try:
        artist = sp.artist(artist_id)
        return artist['genres']
    except Exception as e:
        st.error(f"Error fetching artist genre from Spotify: {e}")
        return []

def get_tracks_by_genre(genre):
    try:
        results = sp.search(q=f"genre:{genre}", type='track', limit=50)
        return [(track['name'], track['artists'][0]['name'], track['album']['name'], track['uri']) for track in results['tracks']['items']]
    except Exception as e:
        st.error(f"Error fetching tracks by genre from Spotify: {e}")
        return []

def recommend_songs(input_song, input_artist, csv_file):
    df = pd.read_csv(csv_file)

    # Step 1: get songs by the same artist from CSV
    same_artist_tracks = df[df['artists'].str.contains(input_artist, case=False, na=False)][['track_name', 'artists', 'album_name']].values.tolist()

    # If same artist songs are not found in CSV, get from Spotify
    if len(same_artist_tracks) < 5:
        artist_id = get_artist_id(input_artist)
        if artist_id:
            same_artist_tracks = get_top_tracks(artist_id)[:5]
        else:
            st.error(f"Artist '{input_artist}' not found on Spotify.")
            return

    # Get artist ID and get same genre and related artist songs
    artist_id = get_artist_id(input_artist)
    genre_tracks, related_artist_tracks = [], []

    if artist_id:
        genres = get_genre(artist_id)
        if genres:
            for genre in genres[:1]:  # Select the primary/main genre
                genre_tracks.extend(get_tracks_by_genre(genre))
            genre_tracks = random.sample(genre_tracks, min(5, len(genre_tracks)))
        related_artist_tracks = get_related_artist_tracks(artist_id)

    # get recommendations if categories have fewer than needed
    all_recommendations = same_artist_tracks[:5] + genre_tracks[:5] + related_artist_tracks[:5]
    all_recommendations = all_recommendations[:15]  # Ensures not more than 15

    # If less than 15, get random tracks from CSV
    if len(all_recommendations) < 15:
        additional_tracks = df[['track_name', 'artists', 'album_name']].sample(15 - len(all_recommendations)).values.tolist()
        all_recommendations.extend(additional_tracks)

    # Randomize recommendations
    random.shuffle(all_recommendations)

    # get track URIs for playlist creation
    track_uris = [track[3] for track in all_recommendations if len(track) > 3]

    # Display recommendations in a table
    recommendations_df = pd.DataFrame(all_recommendations, columns=["Song", "Artist", "Album/Single", "URI"])
    st.subheader("Your Melody Match is Here!!!")
    st.table(recommendations_df.drop(columns=["URI"]))  # Hide URI column in table

    # Prompt for playlist name
    playlist_name = st.text_input("Enter a name for your playlist:")

    # Create Playlist and Recently Played buttons for stream lit
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Create Playlist on Spotify"):
            if playlist_name:
                create_playlist(playlist_name, track_uris)
            else:
                st.error("Please enter a playlist name.")
    with col2:
        if st.button("Show Recently Played Songs"):
            show_recently_played()


def create_playlist(playlist_name, track_uris):  #create a playlist from recs
    try:
        user_id = sp.current_user()["id"]
        playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=True)
        sp.playlist_add_items(playlist_id=playlist["id"], items=track_uris)
        st.success(f"Playlist '{playlist_name}' created successfully!")
        st.write(f"🎶 [Open Playlist on Spotify](https://open.spotify.com/playlist/{playlist['id']})")
    except Exception as e:
        st.error(f"Error creating playlist on Spotify: {e}")

def show_recently_played():
    try:
        # Fetching recently played tracks 
        results = sp.current_user_recently_played(limit=10)
        recently_played_tracks = [(track['track']['name'], track['track']['artists'][0]['name'], track['track']['album']['name'], track['track']['uri']) for track in results['items']]
        recently_played_df = pd.DataFrame(recently_played_tracks, columns=["Song", "Artist", "Album", "URI"])
        st.subheader("Your Recently Played Songs:")
        st.table(recently_played_df.drop(columns=["URI"]))  # To Hide URI column in table
    except Exception as e:
        st.error(f"Error fetching recently played tracks: {e}")


input_song = st.text_input("Enter the song name:")
input_artist = st.text_input("Enter the artist name:")

csv_file = "dataset.csv"  #add dataset path here
if input_artist and input_song:
    recommend_songs(input_song, input_artist, csv_file)
