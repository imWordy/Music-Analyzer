## Testing the API to see if spotify is replying to my request

from api.spotifyClient import SpotifyClient

if __name__ == '__main__':
    client = SpotifyClient()
    print(client.clientId)
    print(client.clientSecret)
    token = client.authenticate()
    print(f"The access token is: {token}")