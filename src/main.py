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
    print("\n--- Spotify Global Top 100 Playlist ---")
    playlist_id = "5ABHKGoOzxkaa28ttQV9sE"  # fixed playlist
    tracks = client.getPlaylistTracks(playlist_id)

    if not tracks:
        print("No tracks found in playlist.")
        return None

    for i, t in enumerate(tracks, start=1):
        print(f"{i}. {t['trackName']} by {t['artistName']} "
              f"(Album: {t['albumName']}, Released: {t['releaseDate']})")

    # Interactive menu
    while True:
        choice = input("\nEnter track number to see details (or 'q' to quit): ").strip()
        if choice.lower() == "q":
            break
        if not choice.isdigit() or not (1 <= int(choice) <= len(tracks)):
            print("Invalid choice. Try again.")
            continue

        selected = tracks[int(choice) - 1]
        print(f"\nSelected: {selected['trackName']} by {selected['artistName']}")

        detail_choice = input("See (1) Song Details or (2) Artist Details? ").strip()
        if detail_choice == "1":
            details = get_track_details(selected["trackID"])
            print("\nSong Details:", details)
        elif detail_choice == "2":
            details = get_artist_details(selected["artistID"])
            print("\nArtist Details:", details)
        else:
            print("Invalid choice.")
    return tracks


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
