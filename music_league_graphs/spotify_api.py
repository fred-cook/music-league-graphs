
import tomli
from pathlib import Path
from typing import Any, Sequence
from datetime import datetime
from itertools import zip_longest

import pandas as pd
import numpy as np
import requests

import music_league_graphs as mlg

with open(Path(mlg.__file__).parent.parent / "secret.toml", "rb") as f:
    secrets = tomli.load(f)



class SpotifyAPI:
    MAX_ARTIST_COUNT = 50
    MAX_SONG_AUDIO_FEATURES = 100
    MAX_TRACKS = 100

    def __init__(self, song_ids: pd.Series):
        self.header = self.get_headers()
        self.df = self.get_track_data(song_ids)
        self.artist_data = self.get_artist_data(self.df["artist_ids"])
        self.df = self.combine_artist_data(self.df, self.artist_data)

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
        chunks = self.chunk_series(song_ids, self.MAX_TRACKS)
        data: list[dict[str, Any]] = []

        for chunk in chunks:
            url = f"https://api.spotify.com/v1/tracks?ids={','.join(chunk)}"
            p = requests.get(url, headers=self.header)
            try:
                p.raise_for_status()
            except requests.HTTPError as e:
                codes = {
                    401: "Bad or expired access token. Re-authenticat user",
                    403: "Bad OAuth request. Check the values in secret.toml",
                    429: "Rate limit exceeded. Try again in a few hours",
                }
                print(codes.get(p.status_code, "Unexpected error code"))
                raise RuntimeError("Couldn't access Spotify API") from e
            data += self.process_tracks(p.json()["tracks"])
        return pd.DataFrame(data)

    def process_tracks(self, tracks: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
        return data
        
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

    def get_artist_data(self, artists: pd.Series) -> dict[str, Any]:
        """
        Every row in the series is a list of artist IDs of length at
        least one. We can bulk retrieve 50 artists at a time from
        spotify, therefore we will convert all of the artists into a 1D
        list and take a set of it, to be split into chunks of 50 + the
        tail end
        """
        # flatten and remove duplicates
        artists: list[str] = list(
            {artist_id for row in artists for artist_id in row}
        )
        artist_chunks = self.chunk_series(artists, self.MAX_ARTIST_COUNT)

        artist_data: dict[str, Any] = {}
        
        for chunk in artist_chunks:
            url = f'https://api.spotify.com/v1/artists?ids={",".join(chunk)}'
            p = requests.get(url, headers=self.header)
            artist_data |= self.process_artist_json(p.json()["artists"])

        return artist_data

    def chunk_series(self, series: Sequence, chunk_size: int) -> list[list[str]]:
        """
        The spotify API for artists can only take a maximum of 50,
        so split it into chunks of 50 + whatever is left over
        """
        split_indices = np.arange(
            chunk_size,
            chunk_size * int(np.ceil(len(series) / chunk_size)),
            chunk_size
        )
        return np.array_split(
            series,
            split_indices
        )
        
    def process_artist_json(self, data: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """
        Process the artist data into a dictionary with the artist IDs as
        the keys so it can be inserted back into the big dataframe
        """
        return {
            artist["id"]: {"genres": artist["genres"],
                           "followers": artist["followers"]["total"],
                           "popularity": artist["popularity"]}
            for artist in data
        }
    
    def combine_artist_data(
            self, df: pd.DataFrame, artist_data: dict[str, Any]
        ) -> pd.DataFrame:
        """
        Recombine the artist data into the main dataframe by using the
        artist id
        """
        artist_df_data: list[dict[str, Any]] = []
        for artist_ids in df["artist_ids"]:
            row = {"genres": list({genre for artist_id in artist_ids
                                 for genre in artist_data[artist_id]["genres"]}),
                "followers": max([artist_data[artist_id]["followers"] for artist_id in artist_ids]),
                "popularity": max([artist_data[artist_id]["popularity"] for artist_id in artist_ids]),
                }
            artist_df_data.append(row)
        return pd.concat((df, pd.DataFrame(artist_df_data)), axis=1)

    def get_track_audio_features(self, track_ids: pd.Series) -> pd.DataFrame:
        """
        Another API to get some Spotify ownbrand stats like danceability
        and valence (?)

        Deprecated November 2024
        """
        chunks = self.chunk_series(track_ids, self.MAX_SONG_AUDIO_FEATURES)

        feature_keys = [
            "acousticness", # A confidence measure from 0.0 to 1.0 of whether the track is acoustic
            "danceability", # Danceability describes how suitable a track is for dancing based on a combination of musical elements including tempo, rhythm stability, beat strength, and overall regularity.
            "energy", # Energy is a measure from 0.0 to 1.0 and represents a perceptual measure of intensity and activity. 
            "instrumentalness", # Predicts whether a track contains no vocals. "Ooh" and "aah" sounds are treated as instrumental 
            "key", # The key the track is in. Integers map to pitches using standard Pitch Class notation. E.g. 0 = C, 1 = C♯/D♭, 2 = D, and so on. If no key was detected, the value is -1.'
            "liveness", # Detects the presence of an audience in the recording
            "loudness", # The overall loudness of a track in decibels (dB). Loudness values are averaged across the entire track
            "tempo", # The overall estimated tempo of a track in beats per minute (BPM).
            "time_signature", # An estimated time signature. The time signature ranges from 3 to 7 indicating time signatures of "3/4", to "7/4".
            "valence", #A measure from 0.0 to 1.0 describing the musical positiveness conveyed by a track
        ]

        data: list[dict[str, Any]] = []

        for chunk in chunks:
            url = f"https://api.spotify.com/v1/audio-features?ids={','.join(chunk)}"
            p = requests.get(url, headers=self.header)
            print(p.json())
            for track in p.json()["audio_features"]:
                data.append([track[key] for key in feature_keys])
        return pd.DataFrame(data)

