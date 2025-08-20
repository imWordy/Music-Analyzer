## Testing the API to see if Spotify is replying to my request

from api.spotifyClient import SpotifyClient

if __name__ == '__main__':
    client = SpotifyClient()

    print("Choose your authentication method:")
    print("1. Client Credentials Flow")
    print("2. User Login")
    choice = input("Enter 1 or 2: ")

    if choice == "1":
        token = client.authenticate()
        print("Authenticated using Client Credentials Flow")
    elif choice == "2":
        token = client.authenticateUser()
        print("Authenticated using User Login Flow")
    else:
        print("Invalid choice, defaulting to Client Credentials Flow")
        token = client.authenticate()

    tracks = client.searchTrack("Idol", limit=3)
    print("\nSearch results: ")
    for t in tracks:
        print(f"{t['trackName']} by {t['artistName']} "
              f"(Album: {t['albumName']}, Released: {t['releaseDate']})")

    if tracks:
        trackID = tracks[0]['trackID']
        print(f"\nFetching details for track: {tracks[0]['trackName']}")
        songDetails = client.getSongDetails(trackID)
        print("Song Details:", songDetails)

        artistID = tracks[0]['artistID']
        print(f"\nFetching details for artist: {tracks[0]['artistName']}")
        artistDetails = client.getArtistDetails(artistID)
        print("Artist Details:", artistDetails)

    if choice == "2":
        print("\nFetching your recently played tracks...")
        recent = client.getRecentlyPlayed(limit=5)
        for item in recent:
            track = item["track"]
            print(f"- {track['name']} by {track['artists'][0]['name']} "
                  f"(Played at: {item['played_at']})")

        print("\nFetching your top 5 tracks (last 6 months)...")
        topTracks = client.getTopItems(item_type="tracks", time_range="medium_term", limit=5)
        for t in topTracks:
            print(f"- {t['name']} by {t['artists'][0]['name']} (Popularity: {t['popularity']}/100)")

        print("\nFetching your top 5 artists (last 6 months)...")
        topArtists = client.getTopItems(item_type="artists", time_range="medium_term", limit=5)
        for a in topArtists:
            print(f"- {a['name']} (Genres: {', '.join(a['genres']) if a['genres'] else 'Unknown'})")
