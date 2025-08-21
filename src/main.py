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

def search_tracks(query="Blinding Lights", limit=3):
    return client.searchTrack(query, limit)

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



## CLI For current testing phase

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

    tracks = search_tracks("Blinding Lights", limit=3)
    print("\nSearch results: ")
    for t in tracks:
        print(f"{t['trackName']} by {t['artistName']} "
              f"(Album: {t['albumName']}, Released: {t['releaseDate']})")

    if tracks:
        trackID = tracks[0]['trackID']
        songDetails = get_track_details(trackID)
        artistDetails = get_artist_details(tracks[0]['artistID'])
        print("\nSong Details:", songDetails)
        print("Artist Details:", artistDetails)

    if auth["method"] == "user_login":
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
