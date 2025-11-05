from typing import Tuple, List

import psycopg2
from . import DB_connect

class DB_api(DB_connect.DB_connect):
    """
    Class to interact with the database.
    """

    def __init__(self):
        """
        Initializes the DB_api class by calling the parent DB_connect constructor.
        """
        super().__init__()

    def _execute_query(self, query: str, data: Tuple = None, commit: bool = False) -> bool:
        """
        Executes a single SQL query with optional data and commit.
        
        Args:
            query (str): The SQL query to execute.
            data (Tuple, optional): The data to pass to the query. Defaults to None.
            commit (bool, optional): Whether to commit the transaction. Defaults to False.
        
        Returns:
            bool: True if the query executed successfully, False otherwise.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn:
                with conn.cursor() as cur:
                    cur.execute(query, data)
                if commit:
                    conn.commit()
                return True
        except (psycopg2.DatabaseError, Exception) as e:
            print(f"Database error: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.put_connection(conn)

    def _execute_fetch_query(self, query: str, data: Tuple = None) -> List:
        """
        Executes a fetch SQL query and returns the results.
        
        Args:
            query (str): The SQL query to execute.
            data (Tuple, optional): The data to pass to the query. Defaults to None.
        
        Returns:
            List: The fetched results as a list of tuples.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn:
                with conn.cursor() as cur:
                    cur.execute(query, data)
                    return cur.fetchall()
        except (psycopg2.DatabaseError, Exception) as e:
            print(f"Database error: {e}")
            return []
        finally:
            if conn:
                self.put_connection(conn)
        return []

    def _execute_many_query(self, query: str, data: List[Tuple], commit: bool = False) -> bool:
        """
        Executes a SQL query for multiple sets of data using executemany.
        
        Args:
            query (str): The SQL query to execute.
            data (List[Tuple]): List of tuples containing data for each execution.
            commit (bool, optional): Whether to commit the transaction. Defaults to False.
        
        Returns:
            bool: True if the query executed successfully, False otherwise.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn:
                with conn.cursor() as cur:
                    cur.executemany(query, data)
                if commit:
                    conn.commit()
                return True
        except (psycopg2.DatabaseError, Exception) as e:
            print(f"Database error: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.put_connection(conn)

    def get_top_hundred_with_artist_info(self) -> list:
        """
        Retrieves all track IDs and artist IDs from the top_hundered_tracks table.
        
        Returns:
            list: List of tuples containing track IDs and artist IDs.
        """
        query = """
            SELECT t.trackid, ti.artistid 
            FROM top_hundered_tracks t
            JOIN trackinfo ti ON t.trackid = ti.trackid;
        """
        return self._execute_fetch_query(query)

    def get_top_hundred_tracks_for_display(self) -> list:
        """
        Retrieves top 100 tracks with track name, artist name, album name, and release date.
        
        Returns:
            list: List of tuples containing track name, artist name, album name, and release date.
        """
        query = """
            SELECT ti.trackname, ti.artistname, t.albumname, t.releasedate
            FROM top_hundered_tracks t
            JOIN trackinfo ti ON t.trackid = ti.trackid;
        """
        return self._execute_fetch_query(query)

    def get_track_infos(self, track_ids: List[str]) -> list:
        """
        Retrieves track information for a given list of track IDs.

        Args:
            track_ids (List[str]): A list of track IDs.

        Returns:
            list: List of tuples containing track information for the specified tracks.
        """
        query = """
            SELECT *
            FROM trackinfo
            WHERE trackid = ANY(%s);
        """
        return self._execute_fetch_query(query, (track_ids,))

    def get_all_tracks(self) -> list:
        """
        Retrieves all tracks from the trackinfo table.

        Returns:
            list: List of tuples containing all tracks.
        """
        query = "SELECT trackid, trackname, artistname FROM trackinfo;"
        return self._execute_fetch_query(query)

    def get_training_data(self) -> list:
        """
        Retrieves the training data for the genre classification model.

        Returns:
            list: List of tuples containing the training data.
        """
        query = """
            SELECT 
                af.danceability, af.energy, af.key, af.loudness, af.mode, 
                af.speechiness, af.acousticness, af.instrumentalness, af.liveness, 
                af.valence, af.tempo, ad.genres
            FROM audio_features af
            JOIN trackinfo ti ON af.trackid = ti.trackid
            JOIN artistdetails ad ON ti.artistid = ad.artistid
            WHERE ad.genres IS NOT NULL AND ad.genres != '{}';
        """
        return self._execute_fetch_query(query)

    def insert_user_info(self, data: str) -> bool:
        """
        Inserts a new user into the user_info table.
        
        Args:
            data (str): The username to insert.
        
        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        query = "insert into user_info (username) values (%s)"
        return self._execute_query(query, (data,), commit=True)

    def insert_track_info(self, data: Tuple) -> bool:
        """
        Inserts track information into the trackinfo table.
        
        Args:
            data (Tuple): Tuple containing trackid, trackname, artistname, artistid, releasedate.
        
        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        query = """
            INSERT INTO trackinfo (trackid, trackname, artistname, artistid, releasedate) 
            VALUES (%s, %s, %s, %s, %s) 
            ON CONFLICT (trackid) DO NOTHING
        """
        return self._execute_query(query, data, commit=True)

    def insert_track_infos_bulk(self, data: List[Tuple]) -> bool:
        """
        Bulk inserts multiple track information records into the trackinfo table.
        
        Args:
            data (List[Tuple]): List of tuples containing track information.
        
        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        query = """
            INSERT INTO trackinfo (trackid, trackname, artistname, artistid, releasedate) 
            VALUES (%s, %s, %s, %s, %s) 
            ON CONFLICT (trackid) DO NOTHING
        """
        return self._execute_many_query(query, data, commit=True)

    def insert_song_details(self, data: Tuple) -> bool:
        """
        Inserts song details into the songdetails table.
        
        Args:
            data (Tuple): Tuple containing song details fields.
        
        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        query = """
            INSERT INTO songdetails (trackid, trackname, artistname, albumname, releasedate, durationms, popularity, explicit, tracknumber, discnumber, previewurl, spotifyurl) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (trackid) DO NOTHING
        """
        return self._execute_query(query, data, commit=True)

    def insert_artist_details(self, data: Tuple) -> bool:
        """
        Inserts artist details into the artistdetails table.
        
        Args:
            data (Tuple): Tuple containing artist details fields.
        
        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        query = """
            INSERT INTO artistdetails (artistid, artistname, genres, popularity, followers, spotifyurl) 
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (artistid) DO NOTHING
        """
        return self._execute_query(query, data, commit=True)

    def insert_top_hundred_tracks(self, data: List[Tuple]) -> bool:
        """
        Bulk inserts top 100 tracks into the top_hundered_tracks table.
        
        Args:
            data (List[Tuple]): List of tuples containing track information.
        
        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        query = """
            INSERT INTO top_hundered_tracks (trackid, albumname, releasedate) 
            VALUES (%s, %s, %s)
            ON CONFLICT (trackid) DO NOTHING
        """
        insert_data = [(d[0], d[3], d[4]) for d in data]
        return self._execute_many_query(query, insert_data, commit=True)

    def insert_albums(self, data: Tuple) -> bool:
        """
        Inserts album information into the albums table.
        
        Args:
            data (Tuple): Tuple containing album information fields.
        
        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        query = """
            INSERT INTO albums (albumid, albumname, releasedate, artistid, spotifyurl, totaltracks)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (albumid) DO NOTHING
        """
        return self._execute_query(query, data, commit=True)
        
    def insert_song_popularity(self, data: Tuple) -> bool:
        """
        Inserts or updates song popularity in the song_popularity table.
        
        Args:
            data (Tuple): Tuple containing trackid and popularity.
        
        Returns:
            bool: True if insertion/update was successful, False otherwise.
        """
        query = """
            INSERT INTO song_popularity (trackid, popularity)
            VALUES (%s, %s)
            ON CONFLICT (trackid) DO UPDATE SET popularity = EXCLUDED.popularity
        """
        return self._execute_query(query, data, commit=True)

    def insert_artist_popularity(self, data: Tuple) -> bool:
        """
        Inserts or updates artist popularity in the artist_popularity table.
        
        Args:
            data (Tuple): Tuple containing artistid and popularity.
        
        Returns:
            bool: True if insertion/update was successful, False otherwise.
        """
        query = """
            INSERT INTO artist_popularity (artistid, popularity)
            VALUES (%s, %s)
            ON CONFLICT (artistid) DO UPDATE SET popularity = EXCLUDED.popularity
        """
        return self._execute_query(query, data, commit=True)

    def insert_artist_genre(self, data: Tuple) -> bool:
        """
        Inserts artist genre into the artist_genres table.
        
        Args:
            data (Tuple): Tuple containing artistid and genre.
        
        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        query = """
            INSERT INTO artist_genres (artistid, genre)
            VALUES (%s, %s)
            ON CONFLICT (artistid, genre) DO NOTHING
        """
        return self._execute_query(query, data, commit=True)

    def insertmany_audio_features(self, data: List[Tuple]) -> bool:
        """
        Inserts audio features for multiple tracks into the audio_features table.

        Args:
            data (List[Tuple]): List of tuples containing audio feature fields for each track.

        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        query = """
            INSERT INTO audio_features (spotify_track_id, trackid, danceability, energy, key, loudness, mode, speechiness, acousticness, instrumentalness, liveness, valence, tempo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (spotify_track_id) DO NOTHING
        """
        return self._execute_many_query(query, data, commit=True)

    def get_audio_features_for_top_100(self) -> list:
        """
        Retrieves audio features for the top 100 tracks.

        Returns:
            list: List of tuples containing audio features for the top 100 tracks.
        """
        query = """
            SELECT af.*
            FROM audio_features af
            JOIN top_hundered_tracks tht ON af.trackid = tht.trackid;
        """
        return self._execute_fetch_query(query)

    def get_audio_features_for_tracks(self, track_ids: List[str]) -> list:
        """
        Retrieves audio features for a given list of track IDs.

        Args:
            track_ids (List[str]): A list of track IDs.

        Returns:
            list: List of tuples containing audio features for the specified tracks.
        """
        query = """
            SELECT af.*
            FROM audio_features af
            WHERE af.trackid = ANY(%s);
        """
        return self._execute_fetch_query(query, (track_ids,))

    def close_pool(self):
        """
        Closes all connections in the connection pool.
        """
        if self:
            self.closeall()