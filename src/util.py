import base64
import os

import requests
from dotenv import load_dotenv


def get_spotify_bearer():
    """
    Get Spotify bearer token using refresh token from .env.

    Returns:
        str: The bearer token
    """
    load_dotenv()

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")

    if not client_id or not client_secret:
        raise ValueError("Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables")

    if not refresh_token:
        raise ValueError(
            "Spotify refresh token not found in .env file. "
            "Please run 'uv run src/add_refreshtoken_to_env.py' to set up your Spotify credentials."
        )

    auth_b64 = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        headers={
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    return response.json()["access_token"]


def create_spotify_playlist(track_ids: list[str], playlist_name: str) -> str:
    """
    Create a Spotify playlist with the given track IDs.

    Args:
        track_ids (list[str]): List of Spotify track IDs to add to the playlist
        playlist_name (str): Name of the playlist to create

    Returns:
        str: URL of the created playlist
    
    Raises:
        RuntimeError: If any API request fails
    """
    headers = {"Authorization": f"Bearer {get_spotify_bearer()}", "Content-Type": "application/json"}

    # Get user ID
    user_response = requests.get("https://api.spotify.com/v1/me", headers=headers)
    if not user_response.ok:
        raise RuntimeError(f"Failed to get user info: {user_response.status_code} - {user_response.text}")
    user_id = user_response.json()["id"]

    # Create playlist
    playlist_response = requests.post(
        f"https://api.spotify.com/v1/users/{user_id}/playlists",
        headers=headers,
        json={"name": playlist_name, "public": False},
    )
    if not playlist_response.ok:
        raise RuntimeError(f"Failed to create playlist: {playlist_response.status_code} - {playlist_response.text}")
    playlist_id = playlist_response.json()["id"]

    # Add tracks to playlist in batches of 100
    batch_size = 100
    for i in range(0, len(track_ids), batch_size):
        batch = track_ids[i:i + batch_size]
        tracks_response = requests.post(
            f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
            headers=headers,
            json={"uris": [f"spotify:track:{track_id}" for track_id in batch]},
        )
        if not tracks_response.ok:
            raise RuntimeError(f"Failed to add tracks: {tracks_response.status_code} - {tracks_response.text}")

    return f"https://open.spotify.com/playlist/{playlist_id}"

