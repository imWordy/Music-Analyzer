import os
import sys
import threading

from requests import session

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.spotifyClient import SpotifyClient
from DataBase.DB_api import DB_api

class Session:
    def __init__(self):
        """
        Initialize a session, and creates an authentication object.
        """
        self._session = SpotifyClient()

    def authenticate_client(self) -> dict:
        """
        Authenticate using client credentials flow.

        Returns:
            dict: Contains authentication method and token
        """
        token = self._session.authenticate()
        return {"method": "client_credentials", "token": token}

    def authenticate_user(self) -> dict:
        """
        Authenticate using the user login flow

        Returns:
            dict: Contains authentication method and token
        """
        token = self._session.authenticateUser()
        return {"method": "user_login", "token": token}

    @property
    def session(self):
        return self._session


class data_Retrieval():
    def __init__(self, db_api: DB_api, session: Session):
        """
        Defines different methods of data retrieval from spotify

        """
        self.db_api = db_api
        self.session = session

    def search_tracks(self) -> list:
        """
        Search for tracks with optional filters for track name, artist, album, genre and year.

        Returns:
            list: List of matching track results, or None if no results found
        """
        print("\n--- Search Tracks ---")
        query = input("Enter a search query: ").strip()

        # Optional filters
        track_name = input("Filter by track name (optional): ").strip() or None
        artist = input("Filter by artist (optional): ").strip() or None
        album = input("Filter by album (optional): ").strip() or None
        genre = input("Filter by genre (optional): ").strip() or None
        year = input("Filter by year (YYYY or YYYY-YYYY, optional): ").strip() or None

        # If no filters given, fallback to query
        results = self.session.session.searchTrack(
            track=track_name,
            artist=artist,
            album=album,
            genre=genre,
            year=year,
            query=query if not (track_name or artist or album or genre or year) else None,
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

    def get_track_details(self, track_id) -> dict:
        """
        Get detailed information for a specific track.

        Args:
            track_id (str): Spotify track ID

        Returns:
            dict: Track details from Spotify API
        """
        return self.session.session.getSongDetails(track_id)

    def get_artist_details(self, artist_id) -> dict:
        """
        Get detailed information for a specific artist.

        Args:
            artist_id (str): Spotify artist ID

        Returns:
            dict: Artist details from Spotify API
        """
        return self.session.session.getArtistDetails(artist_id)

    def get_recently_played(self, limit=5) -> list:
        """
        Get user's recently played tracks.

        Args:
            limit (int): Maximum number of tracks to return

        Returns:
            list: Recently played tracks
        """
        return self.session.session.getRecentlyPlayed(limit)

    def get_top_tracks(self, limit=5, time_range="medium_term") -> list:
        """
        Get user's top tracks.

        Args:
            limit (int): Maximum number of tracks to return
            time_range (str): Time range to consider ('short_term', 'medium_term', 'long_term')

        Returns:
            list: User's top tracks
        """
        return self.session.session.getTopItems(item_type="tracks", time_range=time_range, limit=limit)

    def get_top_artists(self, limit=5, time_range="medium_term") -> list:
        """
        Get user's top artists.

        Args:
            limit (int): Maximum number of artists to return
            time_range (str): Time range to consider ('short_term', 'medium_term', 'long_term')

        Returns:
            list: User's top artists
        """
        return self.session.session.getTopItems(item_type="artists", time_range=time_range, limit=limit)

    def get_top_100_playlist(self) -> bool:
        """
        Get Spotify Global Top 100 playlist tracks and store in database.

        Returns:
            list: List of tracks from the playlist, or None if no tracks found
        """
        print("\n--- Spotify Global Top 100 Playlist ---")
        playlist_id = "5ABHKGoOzxkaa28ttQV9sE"  # fixed playlist
        playlist_tracks = self.session.session.getPlaylistTracks(playlist_id)

        if not playlist_tracks:
            print("No tracks found in playlist.")
            return False

        print(f"Found {len(playlist_tracks)} tracks. Preparing for bulk insert...")

        tracks_info_to_insert = []
        top_hundred_tracks_to_insert = []

        for track_item in playlist_tracks:
            tracks_info_to_insert.append(
                (
                    track_item['trackID'],
                    track_item['trackName'],
                    track_item['artistName'],
                    track_item['artistID'],
                    track_item['releaseDate']
                )
            )
            top_hundred_tracks_to_insert.append(
                (
                    track_item['trackID'],
                    track_item['trackName'],
                    track_item['artistName'],
                    track_item['albumName'],
                    track_item['releaseDate']
                )
            )

        print("Performing bulk inserts...")
        if tracks_info_to_insert:
            self.db_api.insert_track_infos_bulk(tracks_info_to_insert)

        if top_hundred_tracks_to_insert:
            self.db_api.insert_top_hundred_tracks(top_hundred_tracks_to_insert)

        print("Finished processing top 100 tracks.")
        return True

class data_Processing:
    def __init__(self, db_api: DB_api, session: Session):
        self.db_api = db_api
        self.session = session
        self._lock = threading.Lock()
        self.threads = []

    def thread_init(self, tracks_chunk: list[tuple[str, str]], thread_id: int) -> None:
        thread = threading.Thread(target=self.populate_derived_data, args=(tracks_chunk, thread_id,))
        thread.start()
        self.threads.append(thread)

    def populate_derived_data_threading(self):
        try:
            print("Starting data population process for derived tables...")
            all_tracks = self.db_api.get_top_hundred_with_artist_info()
            if not all_tracks:
                print("No tracks found in 'top_hundered_tracks' to process.")
                return

            divided_tracks = [all_tracks[i * len(all_tracks) // 5: (i + 1) * len(all_tracks) // 5] for i in range(0, 5)]

            print(f"Found {len(all_tracks)} tracks to process.")

            for i in range(5):
                self.thread_init(divided_tracks[i], i)

            for thread in self.threads:
                thread.join()

            print("\nData population process completed successfully.")

        except Exception as e:
            print(f"An error occurred while processing derived data: {e}")

        finally:
            self.db_api.close_pool()
            print("Database connections closed.")

    def populate_derived_data(self, tracks: list[tuple[str, str]], thread_id: int) -> None:
        """
        Fetches detailed information for tracks in the top-100 list and
        populates the derived database tables.
        """
        try:
            # 1. Get all tracks from the top_hundred_tracks table
            for i, (track_id, artist_id) in enumerate(tracks):
                print(f"Thread {thread_id} : Processing track {i + 1}/{len(tracks)} (TrackID: {track_id})...")

                song_details = None
                artist_details = None
                # 2. Get detailed info for the track and artist from Spotify API
                try:
                    song_details = self.session.session.getSongDetails(track_id)
                    artist_details = self.session.session.getArtistDetails(artist_id)
                except Exception as e:
                    print(f"  - Could not fetch details for track {track_id} from API: {e}")

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


class main(Session):
    def __init__(self):
        super().__init__()
        self.db_api = DB_api()
        self.data_Retrieval = data_Retrieval(self.db_api, self)
        self.data_Processing = data_Processing(self.db_api, self)

    def main(self):
        try:
            print("Choose your authentication method:")
            print("1. Client Credentials Flow")
            print("2. User Login")
            choice = input("Enter 1 or 2: ")

            auth = None
            if choice == "1":
                auth = self.authenticate_client()
                print("Authenticated using Client Credentials Flow")
            elif choice == "2":
                auth = self.authenticate_user()
                print("Authenticated using User Login Flow")
            else:
                auth = self.authenticate_client()
                print("Invalid choice, defaulting to Client Credentials Flow")

            # Menu for actions
            print("\n--- Main Menu ---")
            print("1. Search Tracks")
            print("2. Fetch Top 100 Global Playlist")
            if auth and auth.get("method") == "user_login":
                print("3. See Recently Played + Top Tracks/Artists")
            action = input("Enter your choice: ")

            if action == "1":
                searched_tracks = self.data_Retrieval.search_tracks()
                if searched_tracks:
                    trackID = searched_tracks[0]['trackID']
                    songDetails = (self.data_Retrieval.get_track_details(trackID))
                    artistDetails = self.data_Retrieval.get_artist_details(searched_tracks[0]['artistID'])
                    print("\nSong Details:", songDetails)
                    print("Artist Details:", artistDetails)

            elif action == "2":
                self.data_Retrieval.get_top_100_playlist()
                self.data_Processing.populate_derived_data_threading()

            elif action == "3" and auth and auth.get("method") == "user_login":
                recent = self.data_Retrieval.get_recently_played(limit=5)
                topTracks = self.data_Retrieval.get_top_tracks(limit=5)
                topArtists = self.data_Retrieval.get_top_artists(limit=5)

                print("\nRecently Played:")
                for item in recent:
                    track_item = item["track"]
                    print(f"- {track_item['name']} by {track_item['artists'][0]['name']} "
                          f"(Played at: {item['played_at']})")

                print("\nTop Tracks (last 6 months):")
                for t_item in topTracks:
                    print(
                        f"- {t_item['name']} by {t_item['artists'][0]['name']} (Popularity: {t_item['popularity']}/100)")

                print("\nTop Artists (last 6 months):")
                for a_item in topArtists:
                    print(
                        f"- {a_item['name']} (Genres: {', '.join(a_item['genres']) if a_item['genres'] else 'Unknown'})")
        finally:
            # This will ensure the connection pool is closed when the program exits
            if self:
                self.db_api.close_pool()
            print("\nApplication finished and database connections closed.")


if __name__ == "__main__":
    app = main()
    app.main()