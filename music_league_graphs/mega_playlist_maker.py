"""
Given a list of playlists create a single playlist with every track

"""

from spotify_api import SpotifyAPI

playlists = [
    "6bUqMVLPpIy5lDedT9XojU",
    "1cfQvKacH5pqPTqLsryhph",
    "7BNVBKHxZrOIO1eklKqdd5",
    "3J8w6HdrpzauCUo33H7xHj",
    "6aRLeg8gJWnLyha0oYDZLQ",
    "7yp3iUHHGFBcakQTE3h2ml",
    "4gRNXZQcIwCgzGYTTEDGKj",
    "0V1h0PghvnMwaqhgDt2Xc2",
    "4i7mVmMRsl7j18bZYhqLVe",
    "3ZhyvYtdRu7dCUQlwOevbp",
    "67Q8XQU7wtylum5jmrNRym",
    "27TPY1jW5xV2yxXFIHkFw3",
    "4KAgxPt6HfuIFrN6SX5LlX",
    "1kS48FNEasumE88uR8hgze",
    "2g0rjV6LS5ZQXHXO6qOIve",
    "7wsafN78NTAVTCbCefCNK0",
    "26LV3BPclXyNeo32uF4neo",
    "4vSaU1IzOTCQsphmF3QQq7",
    "6tunA0TPOZd3yPjzOAHUCD",
    "44EiidAH4DWHbqCb0QfeRm",
    "3yoCGl4PJUZslFDsbBUcw0",
    "52ao3RG5MyGwZ2BW0mJxMl",
    "6nGobIdEP8HkqXGRwhLZvr",
    "6ldEChPtV5TZffM9cECFI8",
    "3ZQ0X98hWkdVSyEvX6lp6P",
    "0jkGqz0nn9zLVoMw5FtU7y",
    "0NoBVpFfTeMrbbwGHYQLRT",
    "5LjjfkOxbMcVxbVrv60jPQ",
    "6ZxzOrr1p0p7lmubJRNXe2",
    "4ROFXmUQ0HM4vPksuoOMgS",
    "6h0cv9dwvjmEf60dxVIAzo",
    "2B0kuxE9etwnxK08OKm7JH",
]

api = SpotifyAPI()

all_tracks = [
    track for playlist in playlists for track in api.get_playlist(playlist)
]


track_uris = [
    "spotify:track:" + track_id for track_id in all_tracks
]

auth = api.get_playlist_auth()

playlist_id = api.create_playlist(
    auth=auth,
    name="mega playlist",
    description="Every song ever added to risky discs"
)

p = api.add_tracks_to_playlist(
    auth=auth,
    playlist_id=playlist_id,
    tracks=track_uris,
)