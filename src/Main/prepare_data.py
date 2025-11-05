
import pandas as pd
import os
import time
from Main import data_Retrieval, Session

def prepare_data(input_csv_path, output_csv_path):
    """
    Reads a CSV file of tracks, fetches their genres, and saves the data to a new CSV file.

    Args:
        input_csv_path (str): The path to the input CSV file.
        output_csv_path (str): The path to save the output CSV file.
    """
    session = Session()
    session.authenticate_client()
    data_retrieval = data_Retrieval(None, session.session)

    df = pd.read_csv(input_csv_path)
    genres = []
    
    print(f"Starting data preparation. This will take a while as it fetches genre data for {len(df)} tracks.")

    for i, track_id in enumerate(df['track_id']):
        if (i + 1) % 20 == 0:
            print(f"  Processed {i + 1}/{len(df)} tracks...")
        try:
            # Add a small delay to avoid hitting API rate limits
            time.sleep(0.1)
            track_details = data_retrieval.get_track_details(track_id)
            if track_details and 'artists' in track_details and track_details['artists']:
                artist_id = track_details['artists'][0]['id']
                artist_details = data_retrieval.get_artist_details(artist_id)
                if artist_details and 'genres' in artist_details and artist_details['genres']:
                    genres.append(','.join(artist_details['genres']))
                else:
                    genres.append('Unknown')
            else:
                genres.append('Unknown')
        except Exception as e:
            if "429" in str(e):
                print("Rate limit hit. Waiting for 10 seconds before continuing...")
                time.sleep(10)
                # Retry the current track
                i -= 1 
                continue
            print(f"Error fetching details for track {track_id}: {e}")
            genres.append('Unknown')

    df['genre'] = genres
    df.to_csv(output_csv_path, index=False)
    print(f"Data with genres saved to {output_csv_path}")

if __name__ == '__main__':
    input_csv = os.path.join(os.path.dirname(__file__), '..', 'DataBase', 'SpotifyAudioFeaturesApril2019.csv')
    output_csv = os.path.join(os.path.dirname(__file__), '..', 'DataBase', 'SpotifyAudioFeaturesWithGenres.csv')
    prepare_data(input_csv, output_csv)
