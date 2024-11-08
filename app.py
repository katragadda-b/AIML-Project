import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import random
import streamlit as st

# Set up the page config with title and layout options
st.set_page_config(
    page_title="Song Recommender",
    layout="centered",
    initial_sidebar_state="expanded"
)

SPOTIPY_CLIENT_ID = '63268e5ed3e44147bbc532107e5d0780'  
SPOTIPY_CLIENT_SECRET = 'f700fbed7a5a43e2a332dc60bbd0429e'  

auth_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
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
        return [(track['name'], track['artists'][0]['name'], track['album']['name']) for track in top_tracks['tracks']]
    except Exception as e:
        st.error(f"Error fetching top tracks from Spotify: {e}")
        return []

def get_related_artists(artist_id):
    try:
        related = sp.artist_related_artists(artist_id)
        return [artist['id'] for artist in related['artists']]
    except Exception as e:
        st.error(f"Error fetching related artists from Spotify: {e}")
        return []

def recommend_songs(input_song, input_artist, csv_file):
    df = pd.read_csv(csv_file)

    artist_id = get_artist_id(input_artist)
    
    if artist_id:
        same_artist_tracks = get_top_tracks(artist_id)
        same_artist_tracks = random.sample(same_artist_tracks, min(5, len(same_artist_tracks)))

        related_artist_ids = get_related_artists(artist_id)
        related_artist_tracks = []
        for rel_artist_id in related_artist_ids:
            related_artist_tracks.extend(get_top_tracks(rel_artist_id))
        related_artist_tracks = random.sample(related_artist_tracks, min(5, len(related_artist_tracks)))

        all_recommended_tracks = same_artist_tracks + related_artist_tracks
        recommended_track_names = {track[0] for track in all_recommended_tracks}
        csv_recommendations = df[~df['track_name'].isin(recommended_track_names)]
        csv_random_recommendations = csv_recommendations.sample(n=min(5, len(csv_recommendations)))[['track_name', 'artists', 'album_name']].values.tolist()

        all_recommendations = same_artist_tracks + related_artist_tracks + csv_random_recommendations

        random.shuffle(all_recommendations)

        recommendations_df = pd.DataFrame(all_recommendations, columns=["Song", "Artist", "Album/Single"])

        st.subheader("Shuffled Recommendations")
        st.table(recommendations_df)
        
    else:
        st.error(f"Artist '{input_artist}' not found on Spotify.")

input_song = st.text_input("Enter the song name:")
input_artist = st.text_input("Enter the artist name:")

csv_file = "C:/Users/bhumi/Desktop/College/Sem 1 , Y2/AI-ML/project/archive/dataset.csv"   
if input_artist and input_song:
    recommend_songs(input_song, input_artist, csv_file)
