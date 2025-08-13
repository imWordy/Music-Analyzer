import os
from telnetlib import XAUTH

import requests
from dotenv import load_dotenv

class SpotifyClient:
    def __init__(self):
        load_dotenv(dotenv_path="config/.env")

        self.clientId = os.getenv("SPOTIFY_CLIENT_ID")
        self.clientSecret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.tokenUrl = "https://accounts.spotify.com/api/token"
        self.accessToken = None

    def authenticate(self):
        """
        Handles Client Credentials Flow:
        1. Sends clientId and clientSecret to Spotify
        2. Get the access token from Spotify and stores it
        """
        authResponse = requests.post(self.tokenUrl,
                                     data = {"grant_type": "client_credentials"},
                                     auth = (self.clientId, self.clientSecret))
        if authResponse.status_code != 200:
            raise Exception(f"Failed to authenticate with Spotify: {authResponse.status_code}")

        tokenData = authResponse.json()
        self.accessToken = tokenData["access_token"]
        return self.accessToken

    def searchTrack(self, query, limit=10):
        """
        Searches for a track given by user
        """
        pass

    def getAudioFeatures(self, trackId):
        """
        Displays the features for a track
        """
        pass
