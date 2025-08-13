from api.spotifyClient import SpotifyClient

if __name__ == '__main__':
    client = SpotifyClient()
    token = client.authenticate()
    print(f"Access Token: {token}")