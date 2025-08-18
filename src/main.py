## Testing the API to see if Spotify is replying to my request

from api.spotifyClient import SpotifyClient

if __name__ == '__main__':
    client = SpotifyClient()
    token = client.authenticate()

##Searching for the tracks

    tracks = client.searchTrack("Blinding Lights", limit=3)
    print("Search results: ")
    for t in tracks:
        print(f"{t['trackName']} by {t['artistName']} "
              f"(Album: {t['albumName']}, Released: {t['releaseDate']})")

##Getting the details for the track (metadata of first track only)

    if tracks:
        trackID = tracks[0]['trackID']
        print(f"\nFetching details for track: {tracks[0]['trackName']}")
        songDetails = client.getSongDetails(trackID)
        print("Song Details:", songDetails)

##Gets the details of the first artist of that track

        artistID = tracks[0]['artistID']
        print(f"\nFetching details for artist: {tracks[0]['artistName']}")
        artistDetails = client.getArtistDetails(artistID)
        print("Artist Details:", artistDetails)
