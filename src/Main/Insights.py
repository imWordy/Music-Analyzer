from DataBase.DB_api import DB_api

class Insights:
    def __init__(self, db_api: DB_api):
        self.db_api = db_api

    def get_top_artists_by_popularity(self, limit=10):
        """
        Retrieves the top N artists by popularity.
        """
        query = """
            SELECT artistName, popularity, followers, genres
            FROM artistDetails
            ORDER BY popularity DESC
            LIMIT %s;
        """
        return self.db_api._execute_fetch_query(query, (limit,))

    def get_top_tracks_by_popularity(self, limit=10):
        """
        Retrieves the top N tracks by popularity.
        """
        query = """
            SELECT t.trackName, t.artistName, p.popularity
            FROM trackinfo t
            JOIN song_Popularity p ON t.trackID = p.trackID
            ORDER BY p.popularity DESC
            LIMIT %s;
        """
        return self.db_api._execute_fetch_query(query, (limit,))

    def get_genre_popularity_analysis(self):
        """
        Analyzes the popularity of different genres.
        """
        query = """
            SELECT * FROM vw_genre_popularity;
        """
        return self.db_api._execute_fetch_query(query)

    def get_audio_features_analysis(self):
        """
        Provides an analysis of the audio features of the top 100 tracks.
        """
        query = """
            SELECT 
                AVG(a.danceability) as avg_danceability,
                AVG(a.energy) as avg_energy,
                AVG(a.loudness) as avg_loudness,
                AVG(a.speechiness) as avg_speechiness,
                AVG(a.acousticness) as avg_acousticness,
                AVG(a.instrumentalness) as avg_instrumentalness,
                AVG(a.liveness) as avg_liveness,
                AVG(a.valence) as avg_valence,
                AVG(a.tempo) as avg_tempo
            FROM audio_features a
            JOIN top_hundered_tracks t ON a.spotify_track_id = t.trackID;
        """
        return self.db_api._execute_fetch_query(query)

    def get_top_albums_by_avg_track_popularity(self, limit=10):
        """
        Retrieves the top N albums based on the average popularity of their tracks.
        """
        query = """
            SELECT
                sd.albumName,
                ti.artistName,
                AVG(sp.popularity) as avg_track_popularity
            FROM
                songDetails sd
            JOIN trackinfo ti ON sd.trackID = ti.trackID
            JOIN song_Popularity sp ON sd.trackID = sp.trackID
            GROUP BY
                sd.albumName, ti.artistName
            ORDER BY
                avg_track_popularity DESC
            LIMIT %s;
        """
        return self.db_api._execute_fetch_query(query, (limit,))

    def get_artist_track_analysis(self, artist_id: str):
        """
        Provides a summary of an artist's tracks, including average popularity and audio features.
        """
        query = "SELECT * FROM get_artist_track_analysis(%s);"
        return self.db_api._execute_fetch_query(query, (artist_id,))

    def get_user_recommendations(self, user_id: str, limit=10):
        """
        Recommends tracks for a user based on their listening history.
        """
        query = "SELECT * FROM recommend_tracks_for_user(%s, %s);"
        return self.db_api._execute_fetch_query(query, (user_id, limit))
