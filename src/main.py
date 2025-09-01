from api.spotifyClient import SpotifyClient

client = SpotifyClient()

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
    """Fetch Top 100 Spotify songs (as of Aug 8, 2025) from fixed playlist"""
    playlist_id = "5ABHKGoOzxkaa28ttQV9sE"
    print("\nFetching Top 100 Spotify Songs (Aug 8, 2025)...")
    songs = client.getPlaylistTracks(playlist_id)
    for i, song in enumerate(songs, start=1):
        print(f"{i}. {song['trackName']} by {song['artistName']} "
              f"(Album: {song['albumName']}, Released: {song['releaseDate']})")
    return songs

# CLI For current testing phase
if __name__ == '__main__':
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

    # Menu
    print("\nChoose an option:")
    print("1. Search Tracks")
    print("2. Get Top 100 Spotify Songs (Aug 8, 2025)")
    if auth["method"] == "user_login":
        print("3. View Recently Played + Top Tracks/Artists")

    option = input("Enter your choice: ")

    if option == "1":
        tracks = search_tracks()
        if tracks:
            trackID = tracks[0]['trackID']
            songDetails = get_track_details(trackID)
            artistDetails = get_artist_details(tracks[0]['artistID'])
            print("\nSong Details:", songDetails)
            print("Artist Details:", artistDetails)

    elif option == "2":
        get_top_100_playlist()

    elif option == "3" and auth["method"] == "user_login":
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
