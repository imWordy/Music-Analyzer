# Client Setup for Spotify API Happens here

import os
import queue
import requests
from dotenv import load_dotenv
from urllib.parse import urlencode, urlparse, parse_qs
from typing import List, Dict

projectRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
envPath = os.path.join(projectRoot, "config", ".env.example")

class SpotifyClient:
    def __init__(self):
        load_dotenv(dotenv_path=envPath)
        self.clientId = os.getenv("SPOTIFY_CLIENT_ID")
        self.clientSecret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.tokenUrl = "https://accounts.spotify.com/api/token"
        self.redirectUri = os.getenv("SPOTIFY_REDIRECT_URI")
        self.accessToken = None
        self.refreshToken = None

    def authenticate(self) -> str:
        """
        Handles Client Credentials Flow.
        """
        authResponse = requests.post(
            self.tokenUrl,
            data={"grant_type": "client_credentials"},
            auth=(self.clientId, self.clientSecret)
        )
        if authResponse.status_code != 200:
            raise Exception(f"Failed to authenticate with Spotify: {authResponse.status_code}")
        tokenData = authResponse.json()
        self.accessToken = tokenData["access_token"]
        return self.accessToken

    def get_auth_url(self, scope: str = None) -> str:
        """
        Gets the URL for user authentication.
        """
        if scope is None:
            scope = os.getenv("SPOTIFY_SCOPE", "user-read-recently-played user-top-read")

        authUrl = "https://accounts.spotify.com/authorize"
        queryParams = urlencode({
            "client_id": self.clientId,
            "response_type": "code",
            "redirect_uri": self.redirectUri,
            "scope": scope
        })
        return f"{authUrl}?{queryParams}"

    def fetch_token_from_url(self, url: str) -> dict:
        """
        Fetches the access token from the redirect URL.
        """
        query = parse_qs(urlparse(url).query)
        if "code" not in query:
            raise Exception("Authentication failed: No code received.")
        
        code = query["code"][0]

        tokenResponse = requests.post(
            self.tokenUrl,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirectUri
            },
            auth=(self.clientId, self.clientSecret)
        )
        if tokenResponse.status_code != 200:
            raise Exception(f"Failed user authentication: {tokenResponse.status_code} | {tokenResponse.text}")

        tokenData = tokenResponse.json()
        self.accessToken = tokenData["access_token"]
        self.refreshToken = tokenData.get("refresh_token")
        return {"method": "user_login", "token": self.accessToken}

    def refreshAccessToken(self):
        """
        Refreshes the access token using refresh token.
        """
        response = requests.post(
            self.tokenUrl,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refreshToken
            },
            auth=(self.clientId, self.clientSecret)
        )
        if response.status_code != 200:
            raise Exception(f"Failed to refresh token: {response.status_code}")

        tokenData = response.json()
        self.accessToken = tokenData["access_token"]
        return self.accessToken

    def searchTrack(self, track: str = None,
                    artist: str = None,
                    album: str = None,
                    genre: str = None,
                    year: str = None,
                    query: str = None,
                    limit: int = 10) -> List[Dict]:
        """
        Searches for a track on Spotify.
        """
        if not self.accessToken:
            self.authenticate()

        if not any([track, artist, album, genre, year, query]):
            raise ValueError("You must provide at least a query or one filter.")

        queryParts = []
        if track: queryParts.append(f"track:{track}")
        if artist: queryParts.append(f"artist:{artist}")
        if album: queryParts.append(f"album:{album}")
        if genre: queryParts.append(f"genre:{genre}")
        if year: queryParts.append(f"year:{year}")

        finalQuery = " ".join(queryParts) if queryParts else query
        headers = {"Authorization": f"Bearer {self.accessToken}"}
        url = "https://api.spotify.com/v1/search"
        params = {"q": finalQuery.strip(), "type": "track", "limit": limit}

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Searching failed: {response.status_code} | {response.text}")

        items = response.json().get("tracks", {}).get("items", [])
        return [
            {
                "trackID": i["id"],
                "trackName": i["name"],
                "artistName": i["artists"][0]["name"],
                "artistID": i["artists"][0]["id"],
                "albumName": i["album"]["name"],
                "releaseDate": i["album"]["release_date"]
            } for i in items
        ]

    def getSongDetails(self, trackId):
        """Fetch detailed metadata for a specific track."""
        if not self.accessToken:
            self.authenticate()

        headers = {"Authorization": f"Bearer {self.accessToken}"}
        url = f"https://api.spotify.com/v1/tracks/{trackId}"

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Fetching song details failed: {response.status_code}")

        track = response.json()
        if not track or not track.get("album"):
            return None # Return None if track data is incomplete

        return {
            "trackID": track.get("id"),
            "trackName": track.get("name"),
            "artistName": track["artists"][0]["name"],
            "albumName": track["album"]["name"],
            "releaseDate": track["album"]["release_date"],
            "durationMs": track.get("duration_ms"),
            "popularity": track.get("popularity"),
            "explicit": track.get("explicit"),
            "trackNumber": track.get("track_number"),
            "discNumber": track.get("disc_number"),
            "previewUrl": track.get("preview_url"),
            "spotifyUrl": track.get("external_urls", {}).get("spotify"),
            "album": track.get("album")
        }

    def getArtistDetails(self, artistId):
        """Fetch metadata for an artist."""
        if not self.accessToken:
            self.authenticate()

        headers = {"Authorization": f"Bearer {self.accessToken}"}
        url = f"https://api.spotify.com/v1/artists/{artistId}"

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Fetching artist details failed: {response.status_code}")

        artist = response.json()
        return {
            "artistID": artist["id"],
            "artistName": artist["name"],
            "genres": artist.get("genres", []),
            "popularity": artist["popularity"],
            "followers": artist["followers"]["total"],
            "spotifyUrl": artist["external_urls"]["spotify"]
        }

    def getRecentlyPlayed(self, limit=20):
        """
        Fetch user's recently played tracks.
        """
        if not self.accessToken:
            raise Exception("User not authenticated.")

        headers = {"Authorization": f"Bearer {self.accessToken}"}
        url = "https://api.spotify.com/v1/me/player/recently-played"
        params = {"limit": limit}

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Fetching recently played failed: {response.status_code}")

        return response.json().get("items", [])

    def getTopItems(self, item_type="tracks", time_range="medium_term", limit=20):
        """
        Fetch user's top tracks or artists.
        """
        if not self.accessToken:
            raise Exception("User not authenticated.")

        headers = {"Authorization": f"Bearer {self.accessToken}"}
        url = f"https://api.spotify.com/v1/me/top/{item_type}"
        params = {"time_range": time_range, "limit": limit}

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Fetching top {item_type} failed: {response.status_code}")

        return response.json().get("items", [])

    def getPlaylistTracks(self, playlistUrlOrId, limit=100):
        """
        Fetch all tracks from a public playlist.
        """
        if not self.accessToken:
            self.authenticate()

        if "spotify.com" in playlistUrlOrId:
            playlistId = playlistUrlOrId.split("/")[-1].split("?")[0]
        else:
            playlistId = playlistUrlOrId

        headers = {"Authorization": f"Bearer {self.accessToken}"}
        url = f"https://api.spotify.com/v1/playlists/{playlistId}/tracks"
        
        tracks = []
        params = {"limit": 100, "offset": 0}

        while True:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                raise Exception(f"Fetching playlist failed: {response.status_code} | {response.text}")

            data = response.json()
            items = data.get("items", [])
            if not items:
                break

            for i in items:
                track = i.get("track")
                if track and track.get("id"):
                    trackInfo = {
                        "trackID": track["id"],
                        "trackName": track["name"],
                        "artistName": track["artists"][0]["name"],
                        "artistID": track["artists"][0]["id"],
                        "albumName": track["album"]["name"],
                        "releaseDate": track["album"]["release_date"],
                    }
                    tracks.append(trackInfo)

            if data.get("next"):
                params["offset"] += params["limit"]
            else:
                break

        return tracks
