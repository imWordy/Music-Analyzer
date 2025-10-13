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
    def __init__(self, db_api: DB_api, spotify_client: SpotifyClient):
        """
        Defines different methods of data retrieval from spotify

        """
        self.db_api = db_api
        self.spotify_client = spotify_client

    def get_track_details(self, track_id) -> dict:
        """
        Get detailed information for a specific track.

        Args:
            track_id (str): Spotify track ID

        Returns:
            dict: Track details from Spotify API
        """
        return self.spotify_client.getSongDetails(track_id)

    def get_artist_details(self, artist_id) -> dict:
        """
        Get detailed information for a specific artist.

        Args:
            artist_id (str): Spotify artist ID

        Returns:
            dict: Artist details from Spotify API
        """
        return self.spotify_client.getArtistDetails(artist_id)

    def get_recently_played(self, limit=20) -> list:
        """
        Get user's recently played tracks.

        Args:
            limit (int): Maximum number of tracks to return

        Returns:
            list: Recently played tracks
        """
        return self.spotify_client.getRecentlyPlayed(limit)

    def get_top_tracks(self, limit=20, time_range="medium_term") -> list:
        """
        Get user's top tracks.

        Args:
            limit (int): Maximum number of tracks to return
            time_range (str): Time range to consider ('short_term', 'medium_term', 'long_term')

        Returns:
            list: User's top tracks
        """
        return self.spotify_client.getTopItems(item_type="tracks", time_range=time_range, limit=limit)

    def get_top_artists(self, limit=20, time_range="medium_term") -> list:
        """
        Get user's top artists.

        Args:
            limit (int): Maximum number of artists to return
            time_range (str): Time range to consider ('short_term', 'medium_term', 'long_term')

        Returns:
            list: User's top artists
        """
        return self.spotify_client.getTopItems(item_type="artists", time_range=time_range, limit=limit)

    def get_top_100_playlist(self) -> bool:
        """
        Get Spotify Global Top 100 playlist tracks and store in database.

        Returns:
            bool: True if successful, False otherwise.
        """
        playlist_id = "5ABHKGoOzxkaa28ttQV9sE"  # fixed playlist
        playlist_tracks = self.spotify_client.getPlaylistTracks(playlist_id)

        if not playlist_tracks:
            return False

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

        if tracks_info_to_insert:
            self.db_api.insert_track_infos_bulk(tracks_info_to_insert)

        if top_hundred_tracks_to_insert:
            self.db_api.insert_top_hundred_tracks(top_hundred_tracks_to_insert)

        return True

class data_Processing:
    def __init__(self, db_api: DB_api, spotify_client: SpotifyClient):
        self.db_api = db_api
        self.spotify_client = spotify_client
        self._lock = threading.Lock()
        self.threads = []

    def thread_init(self, tracks_chunk: list[tuple[str, str]], thread_id: int) -> None:
        thread = threading.Thread(target=self.populate_derived_data, args=(tracks_chunk, thread_id,))
        thread.start()
        self.threads.append(thread)

    def populate_derived_data_threading(self):
        try:
            all_tracks = self.db_api.get_top_hundred_with_artist_info()
            if not all_tracks:
                print("No tracks found in 'top_hundred_tracks' to process.")
                return

            self.threads = []
            
            num_chunks = min(5, len(all_tracks))
            if num_chunks == 0:
                return
            
            chunk_size = (len(all_tracks) + num_chunks - 1) // num_chunks
            divided_tracks = [all_tracks[i:i + chunk_size] for i in range(0, len(all_tracks), chunk_size)]

            print(f"Found {len(all_tracks)} tracks to process, dividing into {len(divided_tracks)} chunks.")

            for i, chunk in enumerate(divided_tracks):
                self.thread_init(chunk, i)

            for thread in self.threads:
                thread.join()

            print("\nData population process completed successfully.")

        except Exception as e:
            print(f"An error occurred while processing derived data: {e}")

    def populate_derived_data(self, tracks: list[tuple[str, str]], thread_id: int) -> None:
        """
        Fetches detailed information for tracks in the top-100 list and
        populates the derived database tables.
        """
        try:
            for i, (track_id, artist_id) in enumerate(tracks):
                print(f"Thread {thread_id} : Processing track {i + 1}/{len(tracks)} (TrackID: {track_id})...")
                song_details = None
                artist_details = None
                try:
                    song_details = self.spotify_client.getSongDetails(track_id)
                    artist_details = self.spotify_client.getArtistDetails(artist_id)
                except Exception as e:
                    print(f"  - Could not fetch details for track {track_id} from API: {e}")

                if song_details:
                    song_pop_data = (song_details['trackID'], song_details['popularity'])
                    self.db_api.insert_song_popularity(song_pop_data)

                    album = song_details.get('album', {})
                    if album.get('id'):
                        album_data = (
                            album['id'],
                            album['name'],
                            album['release_date'],
                            album.get('artists', [{}])[0].get('id'),
                            album.get('external_urls', {}).get('spotify'),
                            album.get('total_tracks')
                        )
                        self.db_api.insert_albums(album_data)

                if artist_details:
                    artist_data = (
                        artist_details['artistID'],
                        artist_details['artistName'],
                        ",".join(artist_details['genres']),
                        artist_details['popularity'],
                        artist_details['followers'],
                        artist_details['spotifyUrl']
                    )
                    self.db_api.insert_artist_details(artist_data)

                    artist_pop_data = (artist_details['artistID'], artist_details['popularity'])
                    self.db_api.insert_artist_popularity(artist_pop_data)

                    for genre in artist_details.get('genres', []):
                        genre_data = (artist_details['artistID'], genre)
                        self.db_api.insert_artist_genre(genre_data)

        except Exception as e:
            print(f"An error occurred while processing derived data in thread {thread_id}: {e}")


class main(Session):
    def __init__(self):
        super().__init__()
        self.db_api = DB_api()
        self.data_Retrieval = data_Retrieval(self.db_api, self.session)
        self.data_Processing = data_Processing(self.db_api, self.session)

    def close_app(self):
        self.db_api.close_pool()
        print("Application finished and database connections closed.")
