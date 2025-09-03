from api.spotifyClient import SpotifyClient
from DataBase.DB_api import DB_api

def populate_derived_data():
    """
    Fetches detailed information for tracks in the top 100 list and
    populates the derived database tables.
    """
    client = SpotifyClient()
    db_api = DB_api()
    
    # Authenticate the client to get API access
    client.authenticate()
    
    print("Starting data population process for derived tables...")
    
    try:
        # 1. Get all tracks from the top_hundred_tracks table
        tracks = db_api.get_top_hundred_with_artist_info()
        if not tracks:
            print("No tracks found in 'top_hundered_tracks' to process.")
            return
            
        print(f"Found {len(tracks)} tracks to process.")
        
        for i, (track_id, artist_id) in enumerate(tracks):
            print(f"Processing track {i+1}/{len(tracks)} (TrackID: {track_id})...")
            
            # 2. Get detailed info for the track and artist from Spotify API
            try:
                song_details = client.getSongDetails(track_id)
                artist_details = client.getArtistDetails(artist_id)
            except Exception as e:
                print(f"  - Could not fetch details for track {track_id} from API: {e}")
                continue

            # 3. Populate derived tables
            if song_details:
                # Populate song_Popularity
                song_pop_data = (song_details['trackID'], song_details['popularity'])
                db_api.insert_song_popularity(song_pop_data)

                # Populate Albums
                album = song_details.get('album', {})
                if album.get('id'):
                    album_data = (
                        album['id'],
                        album['name'],
                        album['release_date'],
                        album.get('artists', [{}])[0].get('id'), # Artist ID for the album
                        album.get('external_urls', {}).get('spotify'),
                        album.get('total_tracks')
                    )
                    db_api.insert_albums(album_data)

            if artist_details:
                # Populate artistDetails
                artist_data = (
                    artist_details['artistID'],
                    artist_details['artistName'],
                    ",".join(artist_details['genres']), # Genres as a string
                    artist_details['popularity'],
                    artist_details['followers'],
                    artist_details['spotifyUrl']
                )
                db_api.insert_artist_details(artist_data)
                
                # Populate artist_popularity
                artist_pop_data = (artist_details['artistID'], artist_details['popularity'])
                db_api.insert_artist_popularity(artist_pop_data)
                
                # Populate Artist_Genres
                for genre in artist_details.get('genres', []):
                    genre_data = (artist_details['artistID'], genre)
                    db_api.insert_artist_genre(genre_data)

        print("\nData population process completed successfully.")

    finally:
        # 4. Close database connections
        db_api.close_pool()
        print("Database connections closed.")


if __name__ == '__main__':
    populate_derived_data()
