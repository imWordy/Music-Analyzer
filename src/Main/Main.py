import os
import sys
import threading

from requests import session

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.spotifyClient import SpotifyClient
from DataBase.DB_api import DB_api
from api.reccobeatsApi import reccobeats

class Session:
    def __init__(self):
        """
        Initialize a Session for interacting with Spotify.

        Creates the underlying SpotifyClient instance that handles all
        authentication and API requests.
        """
        self._session = SpotifyClient()

    def authenticate_client(self) -> dict:
        """
        Authenticate the app using the Client Credentials flow.

        Returns:
            dict: A payload containing:
                - method (str): Authentication method identifier.
                - token (str): Bearer token for API calls that do not require user scope.
        """
        token = self._session.authenticate()
        return {"method": "client_credentials", "token": token}

    def authenticate_user(self) -> dict:
        """
        Authenticate a user using the Authorization Code (user login) flow.

        Returns:
            dict: A payload containing:
                - method (str): Authentication method identifier.
                - token (str): Bearer token tied to the authenticated user.
        """
        token = self._session.authenticateUser()
        return {"method": "user_login", "token": token}

    @property
    def session(self):
        """
        Spotify client accessor.

        Returns:
            SpotifyClient: The configured Spotify API client.
        """
        return self._session


class data_Retrieval():
    def __init__(self, db_api: DB_api, spotify_client: SpotifyClient):
        """
        Data retrieval utilities for Spotify resources.

        Args:
            db_api (DB_api): Database access layer for persisting fetched data.
            spotify_client (SpotifyClient): Authenticated Spotify client.

        """
        self.db_api = db_api
        self.spotify_client = spotify_client

    def get_track_details(self, track_id) -> dict:
        """
        Get detailed information for a specific track.

        Args:
            track_id (str): Spotify track ID

        Returns:
            dict: Track details as returned by the Spotify API.
        """
        return self.spotify_client.getSongDetails(track_id)

    def get_artist_details(self, artist_id) -> dict:
        """
        Retrieve detailed information for a specific artist.

        Args:
            artist_id (str): Spotify artist ID.

        Returns:
            dict: Artist details as returned by the Spotify API.
        """
        return self.spotify_client.getArtistDetails(artist_id)

    def get_recently_played(self, limit=20) -> list:
        """
        Retrieve the authenticated user's recently played tracks.

        Args:
            limit (int, optional): Maximum number of tracks to return. Defaults to 20.

        Returns:
            list: A list of play history items.
        """
        return self.spotify_client.getRecentlyPlayed(limit)

    def get_top_tracks(self, limit=20, time_range="medium_term") -> list:
        """
        Retrieve the authenticated user's top tracks.

        Args:
            limit (int, optional): Maximum number of tracks to return. Defaults to 20.
            time_range (str, optional): 'short_term' | 'medium_term' | 'long_term'. Defaults to 'medium_term'.

        Returns:
            list: A list of top track items.
        """
        return self.spotify_client.getTopItems(item_type="tracks", time_range=time_range, limit=limit)

    def get_top_artists(self, limit=20, time_range="medium_term") -> list:
        """
        Retrieve the authenticated user's top artists.

        Args:
            limit (int, optional): Maximum number of artists to return. Defaults to 20.
            time_range (str, optional): 'short_term' | 'medium_term' | 'long_term'. Defaults to 'medium_term'.

        Returns:
            list: A list of top artist items.
        """
        return self.spotify_client.getTopItems(item_type="artists", time_range=time_range, limit=limit)

    def get_top_100_playlist(self) -> bool:
        """
        Fetch the Spotify Global Top 100 playlist tracks and persist them.

        Retrieves tracks from a fixed playlist, stores basic track info, and
        saves a snapshot table for the Top 100 list.

        Returns:
            bool: True on success, False when playlist retrieval fails.
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
    
    def getAudioFeatures(self, track_ids: list) -> list:
        """
        Retrieve audio features for multiple tracks using the reccobeats API.

        Args:
            track_ids (list): List of Spotify track IDs.
        Returns:
            list: A list of audio feature dictionaries for the provided track IDs.
        """
        reccobeats_api = reccobeats()
        return reccobeats_api.getmany_Audio_Features(track_ids)

class data_Processing:
    def __init__(self, db_api: DB_api, spotify_client: SpotifyClient, reccobeat: reccobeats):
        """
        Data processing utilities for enriching and persisting derived entities.

        Args:
            db_api (DB_api): Database access layer for writes.
            spotify_client (SpotifyClient): Authenticated Spotify client.
        """
        self.db_api = db_api
        self.spotify_client = spotify_client
        self.reccobeat = reccobeat
        self._lock = threading.Lock()
        self.threads = []

    def thread_init(self, tracks_chunk: list[tuple[str, str]], thread_id: int) -> None:
        """
        Spawn a worker thread to process a chunk of tracks.

        Args:
            tracks_chunk (list[tuple[str, str]]): List of (track_id, artist_id) pairs.
            thread_id (int): Numerical identifier for logging.
        """
        thread = threading.Thread(target=self.populate_derived_data, args=(tracks_chunk, thread_id,))
        thread.start()
        self.threads.append(thread)

    def populate_derived_data_threading(self):
        """
        Populate derived data for Top 100 tracks using multiple threads.

        Splits available tracks into up to 5 chunks, processes each chunk
        concurrently, and waits for completion.
        """
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
        Enrich tracks with song, album, and artist details; persist derived tables.

        For each (track_id, artist_id) pair, fetches details from the Spotify API
        and writes to dedicated database tables such as popularity, songs, albums,
        artists, and artist genres.

        Args:
            tracks (list[tuple[str, str]]): Track and artist identifiers to process.
            thread_id (int): Numerical identifier for logging.
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

                    song_details_data = (
                        song_details['trackID'],
                        song_details['trackName'],
                        song_details['artistName'],
                        song_details['album']['name'],
                        song_details['album']['release_date'],
                        song_details['durationMs'],
                        song_details['popularity'],
                        song_details['explicit'],
                        song_details['trackNumber'],
                        song_details['discNumber'],
                        song_details['previewUrl'],
                        song_details['spotifyUrl']
                    )
                    self.db_api.insert_song_details(song_details_data)

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
        
        try:
            with self._lock:
                print(f"Thread {thread_id} : Retreiving Audio Features for {len(tracks)} tracks.")
                track_ids = [track_id for track_id, _ in tracks]
                audio_features = self.reccobeat.getAudioFeatures(track_ids)
                for feature in audio_features:
                    if feature:  # Ensure feature is not None
                        feature_data = (
                            feature['id'],
                            feature['danceability'],
                            feature['energy'],
                            feature['key'],
                            feature['loudness'],
                            feature['mode'],
                            feature['speechiness'],
                            feature['acousticness'],
                            feature['instrumentalness'],
                            feature['liveness'],
                            feature['valence'],
                            feature['tempo'],
                            feature['duration_ms'],
                            feature['time_signature']
                        )
                        self.db_api.insertmany_audio_features(feature_data)
        
        except Exception as e:
            print(f"An error occurred while retrieving audio features in thread {thread_id}: {e}")

class main(Session):
    def __init__(self):
        """
        Application entry point orchestrating authentication, retrieval, and processing.

        Initializes database access, retrieval helpers, and processing pipelines.
        """
        super().__init__()
        self.db_api = DB_api()
        self.data_Retrieval = data_Retrieval(self.db_api, self.session)
        self.data_Processing = data_Processing(self.db_api, self.session)

    def close_app(self):
        """
        Gracefully shut down the application and close DB connections.
        """
        self.db_api.close_pool()
        print("Application finished and database connections closed.")
