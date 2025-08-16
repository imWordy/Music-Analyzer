#Client Setup for Spotify API Happens here

import os
import requests
from dotenv import load_dotenv

projectRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
envPath = os.path.join(projectRoot, "config", ".env")

class SpotifyClient:
    def __init__(self):
        load_dotenv(dotenv_path=envPath)
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
                                     data={"grant_type": "client_credentials"},
                                     auth = (self.clientId, self.clientSecret))
        if authResponse.status_code != 200:
            raise Exception(f"Failed to authenticate with Spotify: {authResponse.status_code}")
        tokenData = authResponse.json()
        self.accessToken = tokenData["access_token"]
        return self.accessToken

    def searchTrack(self, query, limit=10):
        """
        Searches for a track given by user and should return a list of tracks with
        their name, id and the artist.
        """
        if not self.accessToken:
            self.authenticate()

        headers = {"Authorization": f"Bearer {self.accessToken}"}
        url = f"https://api.spotify.com/v1/search"
        params = {"q": query, "type": "track", "limit": limit}

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"Searching has unfortunately failed: {response.status_code}")

        results = response.json()
        tracks = []

        for i in results.get("tracks", {}).get("items", []):
            trackInfo = {"ID": i["id"],
                         "Name": i["name"],
                         "Artist": i["artists"][0]["name"]}
            tracks.append(trackInfo)

            return tracks

    def getAudioFeatures(self, trackId):
        """
        Displays the features for a track
        """
        pass
