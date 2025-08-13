import os
import requests
from dotenv import load_dotenv

class SpotifyClient:
    def __init__(self):
        load_dotenv()
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
        pass

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
