from typing import Tuple

import psycopg2
from DB_connect import DB_connect

class DB_api:
    """
    Class to interact with the database.
    """
    def __init__(self):
        self.db_instance = DB_connect()

    def insert_user_info(self, data: str) -> bool:
        """
        inserts user info into the database
        :param data: str -> username
        :return:
        """
        try:
            with self.db_instance.pool.getconn() as conn:
                with conn.cursor() as cur:
                    cur.execute("insert into user_info (username) values (%s)", (data,))
                conn.commit()
                return True

        except (psycopg2.DatabaseError, Exception) as e:
            print(f"Error occurred while inserting user info: {e}")
            return False

    def insert_track_info(self, data: Tuple) -> bool:
        """
        inserts track info into the database
        :param data: Tuple -> track_id, track_name, artist_name, artistID, release_date
        :return:
        """
        try:
            with self.db_instance.pool.getconn() as conn:
                with conn.cursor() as cur:
                    cur.execute("insert into track_info (track_id, track_name, artist_name, artistID, release_date) values (%s, %s, %s, %s, %s)", (data))
                conn.commit()
                return True

        except (psycopg2.DatabaseError, Exception) as e:
            print(f"Error occurred while inserting track info: {e}")
            return False

    def insert_song_details(self, data: Tuple) -> bool:
        """
        inserts song details into the database
        :param data:
        :return: Tuple -> track_id, track_name, artist_name, albumName, release_date, duration_ms, popularity, explicit, track_number, disc_number, preview_url, spotify_url
        """
        try:
            with self.db_instance.pool.getconn() as conn:
                with conn.cursor() as cur:
                    cur.execute("insert into song_details (track_id, track_name, artist_name, albumName, release_date, duration_ms, popularity, explicit, track_number, disc_number, preview_url, spotify_url) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (data))
                conn.commit()
                return True

        except (psycopg2.DatabaseError, Exception) as e:
            print(f"Error occurred while inserting song details: {e}")
            return False

    def insert_artist_details(self, data: Tuple) -> bool:
        """
        inserts artist details into the database
        :param data: Tuple -> artist_id, artist_name, genres, popularity, followers, spotify_url
        :return:
        """
        try:
            with self.db_instance.pool.getconn() as conn:
                with conn.cursor() as cur:
                    cur.execute("insert into artist_details (artist_id, artist_name, genres, popularity, followers, spotify_url) values (%s, %s, %s, %s, %s, %s)", (data))
                conn.commit()
                return True

        except (psycopg2.DatabaseError, Exception) as e:
            print(f"Error occurred while inserting artist details: {e}")
            return False

    def insert_albums(self, data: Tuple) -> bool:
        """
        inserts albums into the database
        :param data:
        :return:
        """
