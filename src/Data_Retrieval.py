import threading

from api.spotifyClient import SpotifyClient
from DataBase.DB_api import DB_api


class Data_Retrieval():
    def __init__(self):
        """
        Initialize main class with Spotify client and database API instances.
        """
        self.client = SpotifyClient()
        self.db_api = DB_api()
        self._lock = threading.Lock()
        self.threads = []

    def authenticate_client(self):
        """
        Authenticate using client credentials flow.
        
        Returns:
            dict: Contains authentication method and token
        """
        token = self.client.authenticate()
        return {"method": "client_credentials", "token": token}

    def authenticate_user(self):
        """
        Authenticate using user login flow.
        
        Returns:
            dict: Contains authentication method and token
        """
        token = self.client.authenticateUser()
        return {"method": "user_login", "token": token}

    def search_tracks(self):
        """
        Search for tracks with optional filters for track name, artist, album, genre and year.
        
        Returns:
            list: List of matching track results, or None if no results found
        """
        print("\n--- Search Tracks ---")
        query = input("Enter a search query: ").strip()

        # Optional filters
        track = input("Filter by track name (optional): ").strip() or None
        artist = input("Filter by artist (optional): ").strip() or None
        album = input("Filter by album (optional): ").strip() or None
        genre = input("Filter by genre (optional): ").strip() or None
        year = input("Filter by year (YYYY or YYYY-YYYY, optional): ").strip() or None

        # If no filters given, fallback to query
        results = self.client.searchTrack(
            track=track,
            artist=artist,
            album=album,
            genre=genre,
            year=year,
            query=query if not (track or artist or album or genre or year) else None,
            limit=5
        )

        if not results:
            print("No results found.")
            return None

        print("\nSearch results:")
        for i, t in enumerate(results, start=1):
            print(f"{i}. {t['trackName']} by {t['artistName']} "
                  f"(Album: {t['albumName']}, Released: {t['releaseDate']})")
        return results

    def get_track_details(self, track_id):
        """
        Get detailed information for a specific track.
        
        Args:
            track_id (str): Spotify track ID
            
        Returns:
            dict: Track details from Spotify API
        """
        return self.client.getSongDetails(track_id)

    def get_artist_details(self, artist_id):
        """
        Get detailed information for a specific artist.
        
        Args:
            artist_id (str): Spotify artist ID
            
        Returns:
            dict: Artist details from Spotify API
        """
        return self.client.getArtistDetails(artist_id)

    def get_recently_played(self, limit=5):
        """
        Get user's recently played tracks.
        
        Args:
            limit (int): Maximum number of tracks to return
            
        Returns:
            list: Recently played tracks
        """
        return self.client.getRecentlyPlayed(limit)

    def get_top_tracks(self, limit=5, time_range="medium_term"):
        """
        Get user's top tracks.
        
        Args:
            limit (int): Maximum number of tracks to return
            time_range (str): Time range to consider ('short_term', 'medium_term', 'long_term')
            
        Returns:
            list: User's top tracks
        """
        return self.client.getTopItems(item_type="tracks", time_range=time_range, limit=limit)

    def get_top_artists(self, limit=5, time_range="medium_term"):
        """
        Get user's top artists.
        
        Args:
            limit (int): Maximum number of artists to return
            time_range (str): Time range to consider ('short_term', 'medium_term', 'long_term')
            
        Returns:
            list: User's top artists
        """
        return self.client.getTopItems(item_type="artists", time_range=time_range, limit=limit)

    def get_top_100_playlist(self):
        """
        Get Spotify Global Top 100 playlist tracks and store in database.

        Returns:
            list: List of tracks from the playlist, or None if no tracks found
        """
        print("\n--- Spotify Global Top 100 Playlist ---")
        playlist_id = "5ABHKGoOzxkaa28ttQV9sE"  # fixed playlist
        tracks = self.client.getPlaylistTracks(playlist_id)

        if not tracks:
            print("No tracks found in playlist.")
            return False

        print(f"Found {len(tracks)} tracks. Preparing for bulk insert...")

        tracks_info_to_insert = []
        top_hundred_tracks_to_insert = []

        for track in tracks:
            tracks_info_to_insert.append(
                (
                    track['trackID'],
                    track['trackName'],
                    track['artistName'],
                    track['artistID'],
                    track['releaseDate']
                )
            )
            top_hundred_tracks_to_insert.append(
                (
                    track['trackID'],
                    track['trackName'],
                    track['artistName'],
                    track['albumName'],
                    track['releaseDate']
                )
            )

        print("Performing bulk inserts...")
        if tracks_info_to_insert:
            self.db_api.insert_track_infos_bulk(tracks_info_to_insert)

        if top_hundred_tracks_to_insert:
            self.db_api.insert_top_hundred_tracks(top_hundred_tracks_to_insert)

        print("Finished processing top 100 tracks.")
        return True


    def thread_init(self, tracks: list[tuple[str, str]], threadID: int) -> None:
        thread = threading.Thread(target=self.populate_derived_data, args=(tracks, threadID,))
        thread.start()
        self.threads.append(thread)

    def populate_derived_data_threading(self):
        try:
            print("Starting data population process for derived tables...")
            tracks = self.db_api.get_top_hundred_with_artist_info()
            if not tracks:
                print("No tracks found in 'top_hundered_tracks' to process.")
                return

            divided_tracks = [tracks[i * len(tracks) // 5: (i + 1) * len(tracks) // 5] for i in range(0, 5)]

            print(f"Found {len(tracks)} tracks to process.")

            for i in range(5):
                self.thread_init(divided_tracks[i], i)

            for i in self.threads:
                i.join()

            print("\nData population process completed successfully.")

        except Exception as e:
            print(f"An error occurred while processing derived data: {e}")

        finally:
            self.db_api.close_pool()
            print("Database connections closed.")

    def populate_derived_data(self, tracks: list[tuple[str, str]], threadID: int) -> None:
        """
        Fetches detailed information for tracks in the top 100 list and
        populates the derived database tables.
        """
        try:
            # 1. Get all tracks from the top_hundred_tracks table
            for i, (track_id, artist_id) in enumerate(tracks):
                print(f"Thread {threadID} : Processing track {i + 1}/{len(tracks)} (TrackID: {track_id})...")

                # 2. Get detailed info for the track and artist from Spotify API
                try:
                    song_details = self.client.getSongDetails(track_id)
                    artist_details = self.client.getArtistDetails(artist_id)
                except Exception as e:
                    print(f"  - Could not fetch details for track {track_id} from API: {e}")
                    pass

                # 3. Populate derived tables
                if song_details:
                    # Populate song_Popularity
                    song_pop_data = (song_details['trackID'], song_details['popularity'])
                    self.db_api.insert_song_popularity(song_pop_data)

                    # Populate Albums
                    album = song_details.get('album', {})
                    if album.get('id'):
                        album_data = (
                            album['id'],
                            album['name'],
                            album['release_date'],
                            album.get('artists', [{}])[0].get('id'),  # Artist ID for the album
                            album.get('external_urls', {}).get('spotify'),
                            album.get('total_tracks')
                        )
                        self.db_api.insert_albums(album_data)

                if artist_details:
                    # Populate artistDetails
                    artist_data = (
                        artist_details['artistID'],
                        artist_details['artistName'],
                        ",".join(artist_details['genres']),  # Genres as a string
                        artist_details['popularity'],
                        artist_details['followers'],
                        artist_details['spotifyUrl']
                    )
                    self.db_api.insert_artist_details(artist_data)

                    # Populate artist_popularity
                    artist_pop_data = (artist_details['artistID'], artist_details['popularity'])
                    self.db_api.insert_artist_popularity(artist_pop_data)

                    # Populate Artist_Genres
                    for genre in artist_details.get('genres', []):
                        genre_data = (artist_details['artistID'], genre)
                        self.db_api.insert_artist_genre(genre_data)

        except Exception as e:
            print(f"An error occurred while processing derived data: {e}")

# CLI For current testing phase
if __name__ == '__main__':
    try:
        app = Data_Retrieval()
        print("Choose your authentication method:")
        print("1. Client Credentials Flow")
        print("2. User Login")
        choice = input("Enter 1 or 2: ")

        if choice == "1":
            auth = app.authenticate_client()
            print("Authenticated using Client Credentials Flow")
        elif choice == "2":
            auth = app.authenticate_user()
            print("Authenticated using User Login Flow")
        else:
            auth = app.authenticate_client()
            print("Invalid choice, defaulting to Client Credentials Flow")

        # Menu for actions
        print("\n--- Main Menu ---")
        print("1. Search Tracks")
        print("2. Fetch Top 100 Global Playlist")
        if auth["method"] == "user_login":
            print("3. See Recently Played + Top Tracks/Artists")
        action = input("Enter your choice: ")

        if action == "1":
            tracks = app.search_tracks()
            if tracks:
                trackID = tracks[0]['trackID']
                songDetails = app.get_track_details(trackID)
                artistDetails = app.get_artist_details(tracks[0]['artistID'])
                print("\nSong Details:", songDetails)
                print("Artist Details:", artistDetails)

        elif action == "2":
            app.get_top_100_playlist()
            app.populate_derived_data_threading()

        elif action == "3" and auth["method"] == "user_login":
            recent = app.get_recently_played(limit=5)
            topTracks = app.get_top_tracks(limit=5)
            topArtists = app.get_top_artists(limit=5)

            print("\nRecently Played:")
            for item in recent:
                track = item["track"]
                print(f"- {track['name']} by {track['artists'][0]['name']} "
                      f"(Played at: {item['played_at']})")

            print("\nTop Tracks (last 6 months):")
            for t in topTracks:
                print(f"- {t['name']} by {t['artists'][0]['name']} (Popularity: {t['popularity']}/100)")

            print("\nTop Artists (last 6 months):")
            for a in topArtists:
                print(f"- {a['name']} (Genres: {', '.join(a['genres']) if a['genres'] else 'Unknown'})")
    finally:
        # This will ensure the connection pool is closed when the program exits
        app.db_api.close_pool()
        print("\nApplication finished and database connections closed.")
