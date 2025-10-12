from typing import Tuple, List

import psycopg2
from . import DB_connect

class DB_api(DB_connect.DB_connect):
    """
    Class to interact with the database.
    """
    def __init__(self):
        super().__init__()

    def _execute_query(self, query: str, data: Tuple = None, commit: bool = False) -> bool:
        """
        Private helper method to execute a query and handle connection pooling.
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
        Private helper method to execute a fetch query.
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
        Private helper method to execute a query with executemany and handle connection pooling.
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
        Retrieves all trackIDs and artistIDs from top_hundered_tracks.
        """
        query = """
            SELECT t.trackid, ti.artistid 
            FROM top_hundered_tracks t
            JOIN trackinfo ti ON t.trackid = ti.trackid;
        """
        return self._execute_fetch_query(query)

    def insert_user_info(self, data: str) -> bool:
        query = "insert into user_info (username) values (%s)"
        return self._execute_query(query, (data,), commit=True)

    def insert_track_info(self, data: Tuple) -> bool:
        query = """
            INSERT INTO trackinfo (trackid, trackname, artistname, artistid, releasedate) 
            VALUES (%s, %s, %s, %s, %s) 
            ON CONFLICT (trackid) DO NOTHING
        """
        return self._execute_query(query, data, commit=True)

    def insert_track_infos_bulk(self, data: List[Tuple]) -> bool:
        query = """
            INSERT INTO trackinfo (trackid, trackname, artistname, artistid, releasedate) 
            VALUES (%s, %s, %s, %s, %s) 
            ON CONFLICT (trackid) DO NOTHING
        """
        return self._execute_many_query(query, data, commit=True)

    def insert_song_details(self, data: Tuple) -> bool:
        query = """
            INSERT INTO songdetails (trackid, trackname, artistname, albumname, releasedate, durationms, popularity, explicit, tracknumber, discnumber, previewurl, spotifyurl) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (trackid) DO NOTHING
        """
        return self._execute_query(query, data, commit=True)

    def insert_artist_details(self, data: Tuple) -> bool:
        query = """
            INSERT INTO artistdetails (artistid, artistname, genres, popularity, followers, spotifyurl) 
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (artistid) DO NOTHING
        """
        return self._execute_query(query, data, commit=True)

    def insert_top_hundred_tracks(self, data: List[Tuple]) -> bool:
        query = """
            INSERT INTO top_hundered_tracks (trackid, albumname, releasedate) 
            VALUES (%s, %s, %s)
            ON CONFLICT (trackid) DO NOTHING
        """
        insert_data = [(d[0], d[3], d[4]) for d in data]
        return self._execute_many_query(query, insert_data, commit=True)

    def insert_albums(self, data: Tuple) -> bool:
        query = """
            INSERT INTO albums (albumid, albumname, releasedate, artistid, spotifyurl, totaltracks)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (albumid) DO NOTHING
        """
        return self._execute_query(query, data, commit=True)
        
    def insert_song_popularity(self, data: Tuple) -> bool:
        query = """
            INSERT INTO song_popularity (trackid, popularity)
            VALUES (%s, %s)
            ON CONFLICT (trackid) DO UPDATE SET popularity = EXCLUDED.popularity
        """
        return self._execute_query(query, data, commit=True)

    def insert_artist_popularity(self, data: Tuple) -> bool:
        query = """
            INSERT INTO artist_popularity (artistid, popularity)
            VALUES (%s, %s)
            ON CONFLICT (artistid) DO UPDATE SET popularity = EXCLUDED.popularity
        """
        return self._execute_query(query, data, commit=True)

    def insert_artist_genre(self, data: Tuple) -> bool:
        query = """
            INSERT INTO artist_genres (artistid, genre)
            VALUES (%s, %s)
            ON CONFLICT (artistid, genre) DO NOTHING
        """
        return self._execute_query(query, data, commit=True)

    def close_pool(self):
        if self:
            self.closeall()