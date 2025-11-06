-- Query 6: Find a User's Most Listened-To Genre
SELECT ag.genre,
       COUNT(ulh.trackID) AS listen_count
FROM User_Listening_History ulh
         JOIN
     trackinfo ti ON ulh.trackID = ti.trackID
         JOIN
     Artist_Genres ag ON ti.artistID = ag.artistID
WHERE ulh.userID = (SELECT id FROM user_info WHERE username = 'another_user')
GROUP BY ag.genre
ORDER BY listen_count DESC LIMIT 1;
=======
-- Query 6: Find a User's Most Listened-To Genre
SELECT ag.genre,
       COUNT(ulh.trackID) AS listen_count
FROM User_Listening_History ulh
         JOIN
     trackinfo ti ON ulh.trackID = ti.trackID
         JOIN
     Artist_Genres ag ON ti.artistID = ag.artistID
WHERE ulh.userID = (SELECT id FROM user_info WHERE username = 'another_user')
GROUP BY ag.genre
ORDER BY listen_count DESC LIMIT 1;


-- Views
CREATE OR REPLACE VIEW vw_track_details AS
SELECT
    ti.trackID,
    ti.trackName,
    ti.artistName,
    ad.artistID,
    ti.releaseDate,
    sd.albumName,
    sd.durationMs,
    sp.popularity,
    af.danceability,
    af.energy,
    af.loudness,
    af.speechiness,
    af.acousticness,
    af.instrumentalness,
    af.liveness,
    af.valence,
    af.tempo
FROM
    trackinfo ti
LEFT JOIN songDetails sd ON ti.trackID = sd.trackID
LEFT JOIN artistDetails ad ON ti.artistID = ad.artistID
LEFT JOIN song_Popularity sp ON ti.trackID = sp.trackID
LEFT JOIN audio_features af ON ti.trackID = af.spotify_track_id;

CREATE OR REPLACE VIEW vw_genre_popularity AS
SELECT
    g.genre,
    AVG(p.popularity) AS avg_popularity,
    COUNT(t.trackID) AS track_count
FROM
    Artist_Genres g
JOIN artistDetails a ON g.artistID = a.artistID
JOIN trackinfo t ON a.artistID = t.artistID
JOIN song_Popularity p ON t.trackID = p.trackID
GROUP BY
    g.genre
ORDER BY
    avg_popularity DESC;

-- Stored Procedures (Functions for PostgreSQL)

CREATE OR REPLACE FUNCTION get_artist_track_analysis(p_artist_id VARCHAR)
RETURNS TABLE(
    total_tracks BIGINT,
    avg_popularity NUMERIC,
    avg_danceability FLOAT,
    avg_energy FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(vtd.trackID),
        AVG(vtd.popularity),
        AVG(vtd.danceability),
        AVG(vtd.energy)
    FROM
        vw_track_details vtd
    WHERE
        vtd.artistID = p_artist_id;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION recommend_tracks_for_user(p_user_id UUID, p_limit INT)
RETURNS TABLE(
    trackID VARCHAR,
    trackName VARCHAR,
    artistName VARCHAR,
    popularity INT
) AS $$
BEGIN
    RETURN QUERY
    WITH user_top_artists AS (
        SELECT
            ti.artistID,
            COUNT(*) as listen_count
        FROM
            User_Listening_History ulh
        JOIN trackinfo ti ON ulh.trackID = ti.trackID
        WHERE
            ulh.userID = p_user_id
        GROUP BY
            ti.artistID
        ORDER BY
            listen_count DESC
        LIMIT 5
    ),
    user_listened_tracks AS (
        SELECT ulh.trackID FROM User_Listening_History ulh WHERE ulh.userID = p_user_id
    )
    SELECT
        vtd.trackID,
        vtd.trackName,
        vtd.artistName,
        vtd.popularity
    FROM
        vw_track_details vtd
    WHERE
        vtd.artistID IN (SELECT artistID FROM user_top_artists)
        AND vtd.trackID NOT IN (SELECT trackID FROM user_listened_tracks)
    ORDER BY
        vtd.popularity DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
>>>>>>> REPLACE
