-- Query 1: Top 10 Most Prolific Artists in the Top 100
SELECT ti.artistName,
       COUNT(ti.trackID) AS numberOfTopTracks
FROM trackinfo ti
         JOIN
     top_hundered_tracks tht ON ti.trackID = tht.trackID
GROUP BY ti.artistName
ORDER BY numberOfTopTracks DESC LIMIT 10;


-- Query 2: User's Listening History for Popular Artists
SELECT ui.username,
       ti.trackName,
       ti.artistName
FROM User_Listening_History ulh
         JOIN
     user_info ui ON ulh.userID = ui.id
         JOIN
     trackinfo ti ON ulh.trackID = ti.trackID
WHERE ui.username = 'some_username'
  AND ti.artistID IN (SELECT artistID
                      FROM artist_popularity
                      WHERE popularity > 85);


-- Query 3: Genres with High Average Song Popularity
SELECT ag.genre,
       AVG(sp.popularity) AS average_genre_popularity,
       COUNT(ti.trackID)  AS song_count
FROM Artist_Genres ag
         JOIN
     trackinfo ti ON ag.artistID = ti.artistID
         JOIN
     song_Popularity sp ON ti.trackID = sp.trackID
GROUP BY ag.genre
HAVING AVG(sp.popularity) > 70
   AND COUNT(ti.trackID) >= 5
ORDER BY average_genre_popularity DESC;


-- Query 4: Songs More Popular Than Their Artist's Average
SELECT s_outer.trackName,
       s_outer.artistName,
       sp_outer.popularity
FROM songDetails s_outer
         JOIN
     song_Popularity sp_outer ON s_outer.trackID = sp_outer.trackID
WHERE sp_outer.popularity > (SELECT AVG(sp_inner.popularity)
                             FROM songDetails s_inner
                                      JOIN song_Popularity sp_inner ON s_inner.trackID = sp_inner.trackID
                             WHERE s_inner.artistName = s_outer.artistName);


-- Query 5: Rank Artists by Follower Count Within Each Genre
SELECT ad.artistName,
       ag.genre,
       ad.followers,
       RANK() OVER (PARTITION BY ag.genre ORDER BY ad.followers DESC) AS rank_in_genre
FROM artistDetails ad
         JOIN
     Artist_Genres ag ON ad.artistID = ag.artistID
ORDER BY ag.genre,
         rank_in_genre;


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
