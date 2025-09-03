# Client Setup for Spotify API Happens here

import os
import requests
import webbrowser
from dotenv import load_dotenv
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from typing import Tuple, List, Dict

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
        Handles Client Credentials Flow:
        Only useful for public data (tracks, albums, artists).
        :param:
        :return: access token
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

    def authenticateUser(self, scope: str = None) -> str:
        """
        Handles Authorization Code
        Opens browser for user login and permission grant.
        Required for personal/user-specific data and audio features.
        :param: scope: str -> optional, defaults to "user-read-recently-played user-top-read"
        :return: access token
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
        url = f"{authUrl}?{queryParams}"

        # Container to capture code from redirect
        codeContainer = {}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                query = parse_qs(urlparse(self.path).query)
                if "code" in query:
                    codeContainer["code"] = query["code"][0]
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"Authentication successful. You can close this window now.")
                else:
                    self.send_response(400)
                    self.end_headers()

        # Start temporary server for callback
        server = HTTPServer(("127.0.0.1", 8888), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()

        # Open login page
        webbrowser.open(url)

        # Wait for redirect
        while "code" not in codeContainer:
            pass
        server.shutdown()
        code = codeContainer["code"]

        # Exchange code for tokens
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
            raise Exception(f"Failed user authentication: {tokenResponse.status_code}")

        tokenData = tokenResponse.json()
        self.accessToken = tokenData["access_token"]
        self.refreshToken = tokenData.get("refresh_token")
        return self.accessToken

    def refreshAccessToken(self):
        """
        Refreshes the access token using refresh token.
        Only needed for user login flow.
        :param:
        :return: access token
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
        this function searches the track in the spotify database using any of the given data points
        :param track:
        :param artist:
        :param album:
        :param genre:
        :param year:
        :param query:
        :param limit:
        :return: tracks -> list of dictionaries
        """
        if not self.accessToken:
            self.authenticate()

        if not (track or artist or album or genre or year or query):
            raise ValueError("You must provide at least a query or one filter (track, artist, album, genre, year).")

        queryParts = []
        if track: queryParts.append(f"track:{track}")
        if artist: queryParts.append(f"artist:{artist}")
        if album: queryParts.append(f"album:{album}")
        if genre: queryParts.append(f"genre:{genre}")
        if year: queryParts.append(f"year:{year}")

        finalQuery = " ".join(queryParts) if queryParts else query
        finalQuery = finalQuery.strip()
        print(f"[DEBUG] Final query sent to Spotify: {finalQuery}")

        headers = {"Authorization": f"Bearer {self.accessToken}"}
        url = "https://api.spotify.com/v1/search"
        params = {"q": finalQuery, "type": "track", "limit": limit}

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Searching failed: {response.status_code} | {response.text}")

        results = response.json()
        tracks = []
        items = results.get("tracks", {}).get("items", [])
        if not items:
            return []

        for i in items:
            trackInfo = {
                "trackID": i["id"],
                "trackName": i["name"],
                "artistName": i["artists"][0]["name"],
                "artistID": i["artists"][0]["id"],
                "albumName": i["album"]["name"],
                "releaseDate": i["album"]["release_date"]
            }
            tracks.append(trackInfo)
        return tracks

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
        return {
            "trackID": track["id"],
            "trackName": track["name"],
            "artistName": track["artists"][0]["name"],
            "albumName": track["album"]["name"],
            "releaseDate": track["album"]["release_date"],
            "durationMs": track["duration_ms"],
            "popularity": track["popularity"],
            "explicit": track["explicit"],
            "trackNumber": track["track_number"],
            "discNumber": track["disc_number"],
            "previewUrl": track["preview_url"],
            "spotifyUrl": track["external_urls"]["spotify"]
        }

    def getArtistDetails(self, artistId):
        """Fetch metadata for an artist (name, genres, popularity, followers)."""
        if not self.accessToken:
            self.authenticate()

        headers = {"Authorization": f"Bearer {self.accessToken}"}
        url = f"https://api.spotify.com/v1/artists/{artistId}"

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Fetching artist details failed: {response.status_code}")

        artist = response.json()
        genres = artist.get("genres", []) or ["Unknown"]

        return {
            "artistID": artist["id"],
            "artistName": artist["name"],
            "genres": genres,
            "popularity": artist["popularity"],
            "followers": artist["followers"]["total"],
            "spotifyUrl": artist["external_urls"]["spotify"]
        }

    def getRecentlyPlayed(self, limit=20):
        """
        Fetch user's recently played tracks (up to last 50).
        Requires user login scope: user-read-recently-played
        """
        if not self.accessToken:
            self.authenticateUser()

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
        item_type = "tracks" or "artists"
        time_range = "short_term" (4 weeks), "medium_term" (6 months), "long_term" (years)
        Requires user login scope: user-top-read
        """
        if not self.accessToken:
            self.authenticateUser()

        headers = {"Authorization": f"Bearer {self.accessToken}"}
        url = f"https://api.spotify.com/v1/me/top/{item_type}"
        params = {"time_range": time_range, "limit": limit}

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Fetching top {item_type} failed: {response.status_code}")

        return response.json().get("items", [])

    def getPlaylistTracks(self, playlistUrlOrId, limit=100):
        """
        Fetch all tracks and metadata from a given public playlist.
        Uses Client Credentials Flow (no user login required).
        """
        if not self.accessToken:
            self.authenticate()

        # Extract playlist ID from full URL if needed
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
                if track:
                    trackInfo = {
                        "trackID": track["id"],
                        "trackName": track["name"],
                        "artistName": track["artists"][0]["name"],
                        "artistID": track["artists"][0]["id"],
                        "albumName": track["album"]["name"],
                        "releaseDate": track["album"]["release_date"],
                        "popularity": track.get("popularity"),
                        "spotifyUrl": track["external_urls"]["spotify"]
                    }
                    tracks.append(trackInfo)

            # Pagination check
            if data.get("next"):
                params["offset"] += params["limit"]
            else:
                break

        return tracks
