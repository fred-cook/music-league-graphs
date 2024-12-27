
import tomli
from pathlib import Path
from typing import Any
from datetime import datetime
from itertools import zip_longest

import pandas as pd
import requests

import music_league_graphs as mlg

with open(Path(mlg.__file__).parent.parent / "secret.toml", "rb") as f:
    secrets = tomli.load(f)



class SpotifyAPI:

    def __init__(self, song_ids: pd.Series):
        self.header = self.get_headers()
        tracks = self.get_track_data(song_ids)
        self.df = self.process_tracks(tracks)

    def get_headers(self) -> dict[str, str]:
        """
        Get the access token needed to use the Spotify API
        """
        data = {
            "grant_type": "client_credentials",
            "client_id": secrets.get("client_id", ''),
            "client_secret": secrets.get("secret_token", ''),
        }
        auth_response = requests.post("https://accounts.spotify.com/api/token", data=data)
        access_token = auth_response.json().get("access_token")
        return {"Authorization": f"Bearer {access_token}"}

    def get_track_data(self, song_ids: pd.Series) -> list[dict[str, Any]]:
        """
        Get the track data for the list of song ids. Handle
        the return codes if the authorisation is incorrect.
        """
        url = f'https://api.spotify.com/v1/tracks?ids={",".join(song_ids)}'
        p = requests.get(url, headers=self.header)
        try:
            p.raise_for_status()
        except requests.HTTPError:
            codes = {
                401: "Bad or expired access token. Re-authenticat user",
                403: "Bad OAuth request. Check the values in secret.toml",
                429: "Rate limit exceeded. Try again in a few hours",
            }
            print(codes.get(p.status_code, "Unexpected error code"))
            raise
        tracks = p.json()["tracks"]
        if len(tracks) != len(song_ids):
            raise RuntimeError(f"Expected {len(song_ids)} tracks, but received {len(tracks)}")
        return tracks

    def process_tracks(self, tracks: list[dict[str, Any]]) -> pd.DataFrame:
        """
        Extract the information from the track objects returned
        """
        data = []
        for track in tracks:
            track_data = self.get_album_info(track["album"])
            track_data["duration_s"] = track["duration_ms"] / 1000
            track_data["artist_names"] = [artist["name"] for artist in track["artists"]]
            track_data["artist_ids"] = [artist["id"] for artist in track["artists"]]
            track_data["explicit"] = track["explicit"]
            track_data["popularity"] = track["popularity"]
            track_data["song_name"] = track["name"]
            data.append(track_data)
        return pd.DataFrame(data)
        
    def get_album_info(self, album: dict[str, Any]) -> dict[str, Any]:
        """
        Parse the album information extracting only the useful
        items and the date as a datetime
        """
        release_date = self.parse_release_date(album["release_date"])
        album_name = album["name"]
        return {
            "release_date": release_date,
            "album_name": album_name
        }
    
    @staticmethod
    def parse_release_date(date: str) -> datetime:
        time = ["year", "month", "day"]
        # default unknown days/months to the 1st
        return datetime(
            **{t: int(val)
            for t, val in zip_longest(time, date.split("-"), fillvalue=1)}
        )
