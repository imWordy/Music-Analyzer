from api.spotifyClient import SpotifyClient
from DataBase.DB_api import DB_api

client = SpotifyClient()
db_api = DB_api()

# AUTH FUNCTIONS
def authenticate_client():
    token = client.authenticate()
    return {"method": "client_credentials", "token": token}

def authenticate_user():
    token = client.authenticateUser()
    return {"method": "user_login", "token": token}


# DATA FETCHING FUNCTIONS
def search_tracks():
    print("\n--- Search Tracks ---")
    query = input("Enter a search query: ").strip()

    # Optional filters
    track = input("Filter by track name (optional): ").strip() or None
    artist = input("Filter by artist (optional): ").strip() or None
    album = input("Filter by album (optional): ").strip() or None
    genre = input("Filter by genre (optional): ").strip() or None
    year = input("Filter by year (YYYY or YYYY-YYYY, optional): ").strip() or None

    # If no filters given, fallback to query
    results = client.searchTrack(
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


def get_track_details(track_id):
    return client.getSongDetails(track_id)

def get_artist_details(artist_id):
    return client.getArtistDetails(artist_id)

def get_recently_played(limit=5):
    return client.getRecentlyPlayed(limit)

def get_top_tracks(limit=5, time_range="medium_term"):
    return client.getTopItems(item_type="tracks", time_range=time_range, limit=limit)

def get_top_artists(limit=5, time_range="medium_term"):
    return client.getTopItems(item_type="artists", time_range=time_range, limit=limit)

def get_top_100_playlist():
    print("\n--- Spotify Global Top 100 Playlist ---")
    playlist_id = "5ABHKGoOzxkaa28ttQV9sE"  # fixed playlist
    tracks = client.getPlaylistTracks(playlist_id)

    if not tracks:
        print("No tracks found in playlist.")
        return None

    print(f"Found {len(tracks)} tracks. Processing and storing...")

    for track in tracks:
        # 1. Store primary track info (MUST be first to satisfy FK constraints)
        # This may fail if the track already exists (unique constraint), which is okay.
        track_info_data = (
            track['trackID'],
            track['trackName'],
            track['artistName'],
            track['artistID'],
            track['releaseDate']
        )
        db_api.insert_track_info(track_info_data)

        # 2. Store info in top_hundred_tracks, which references trackinfo
        top_track_data = (
            track['trackID'],
            track['trackName'],
            track['artistName'],
            track['albumName'],
            track['releaseDate']
        )
        db_api.insert_top_hundred_track(top_track_data)

        # 3. Get and store detailed song info
        try:
            details = get_track_details(track["trackID"])
            song_details_data = (
                details['trackID'],
                details['trackName'],
                details['artistName'],
                details['albumName'],
                details['releaseDate'],
                details['durationMs'],
                details['popularity'],
                details['explicit'],
                details['trackNumber'],
                details['discNumber'],
                details['previewUrl'],
                details['spotifyUrl']
            )
            db_api.insert_song_details(song_details_data)
        except Exception as e:
            print(f"Could not fetch or store details for track {track['trackName']}: {e}")

    print("Finished processing top 100 tracks.")
    return tracks

# CLI For current testing phase
if __name__ == '__main__':
    try:
        print("Choose your authentication method:")
        print("1. Client Credentials Flow")
        print("2. User Login")
        choice = input("Enter 1 or 2: ")

        if choice == "1":
            auth = authenticate_client()
            print("Authenticated using Client Credentials Flow")
        elif choice == "2":
            auth = authenticate_user()
            print("Authenticated using User Login Flow")
        else:
            auth = authenticate_client()
            print("Invalid choice, defaulting to Client Credentials Flow")

        # Menu for actions
        print("\n--- Main Menu ---")
        print("1. Search Tracks")
        print("2. Fetch Top 100 Global Playlist")
        if auth["method"] == "user_login":
            print("3. See Recently Played + Top Tracks/Artists")
        action = input("Enter your choice: ")

        if action == "1":
            tracks = search_tracks()
            if tracks:
                trackID = tracks[0]['trackID']
                songDetails = get_track_details(trackID)
                artistDetails = get_artist_details(tracks[0]['artistID'])
                print("\nSong Details:", songDetails)
                print("Artist Details:", artistDetails)

        elif action == "2":
            get_top_100_playlist()

        elif action == "3" and auth["method"] == "user_login":
            recent = get_recently_played(limit=5)
            topTracks = get_top_tracks(limit=5)
            topArtists = get_top_artists(limit=5)

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
        db_api.close_pool()
        print("\nApplication finished and database connections closed.")