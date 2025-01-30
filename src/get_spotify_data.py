import json
import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from tqdm import tqdm


def fetch_tracks_data(track_ids, headers):
    """Fetch multiple tracks data from Spotify API in a single request"""
    url = "https://api.spotify.com/v1/tracks"
    params = {"ids": ",".join(track_ids)}
    response = requests.get(url, headers=headers, params=params)
    time.sleep(0.1)

    if response.status_code == 429:  # Rate limit exceeded
        retry_after = int(response.headers.get("Retry-After", 1))
        time.sleep(retry_after)
        return fetch_tracks_data(track_ids, headers)
    
    if response.status_code == 401:  # Invalid token
        raise ValueError("Invalid or expired Spotify token. Please refresh your token.")

    response.raise_for_status()
    return response.json()["tracks"]


def fetch_albums_data(album_ids, headers):
    """Fetch multiple albums data from Spotify API in a single request"""
    url = "https://api.spotify.com/v1/albums"
    params = {"ids": ",".join(album_ids)}
    response = requests.get(url, headers=headers, params=params)
    time.sleep(0.1)

    if response.status_code == 429:  # Rate limit exceeded
        retry_after = int(response.headers.get("Retry-After", 1))
        time.sleep(retry_after)
        return fetch_albums_data(album_ids, headers)
    
    if response.status_code == 401:  # Invalid token
        raise ValueError("Invalid or expired Spotify token. Please refresh your token.")

    response.raise_for_status()
    return response.json()["albums"]


def fetch_artists_data(artist_ids, headers):
    """Fetch multiple artists data from Spotify API in a single request"""
    url = "https://api.spotify.com/v1/artists"
    params = {"ids": ",".join(artist_ids)}
    response = requests.get(url, headers=headers, params=params)
    time.sleep(0.1)

    if response.status_code == 429:  # Rate limit exceeded
        retry_after = int(response.headers.get("Retry-After", 1))
        time.sleep(retry_after)
        return fetch_artists_data(artist_ids, headers)
    
    if response.status_code == 401:  # Invalid token
        raise ValueError("Invalid or expired Spotify token. Please refresh your token.")

    response.raise_for_status()
    return response.json()["artists"]


def enrich_tracks_data(input_parquet, tracks_path, headers):
    """
    Fetch additional track data from Spotify API and save as JSON files

    Args:
        input_csv: Path to the input CSV file containing track IDs
        tracks_path: Path to save the track JSON files
        headers: Spotify API headers with authentication token
    """
    # Create output directory
    tracks_path.mkdir(parents=True, exist_ok=True)

    # Read CSV file
    df = pd.read_parquet(input_parquet)

    # Get unique IDs
    track_ids = df["track_id"].unique().tolist()
    uncached_track_ids = [i for i in track_ids if not (tracks_path / f"{i}.json").exists()]

    # Process tracks
    if uncached_track_ids:
        for i in tqdm(range(0, len(uncached_track_ids), 50), desc="Fetching track data"):
            batch_ids = uncached_track_ids[i : i + 50]
            try:
                for j, track_data in enumerate(fetch_tracks_data(batch_ids, headers)):
                    with open(tracks_path / f"{batch_ids[j]}.json", "w") as f:
                        json.dump(track_data, f, indent=2)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching track data: {e}")

    print("all track data fetched")


def enrich_albums_data(albums_path, album_ids, headers):
    """
    Fetch additional album data from Spotify API and save as JSON files

    Args:
        albums_path: Path to save the album JSON files
        album_ids: List of album IDs to fetch
        headers: Spotify API headers with authentication token
    """
    # Create output directory
    albums_path.mkdir(parents=True, exist_ok=True)

    # Filter out already cached albums
    uncached_album_ids = [i for i in album_ids if not (albums_path / f"{i}.json").exists()]

    # Process albums
    if uncached_album_ids:
        for i in tqdm(range(0, len(uncached_album_ids), 20), desc="Fetching album data"):
            batch_ids = uncached_album_ids[i : i + 20]
            try:
                for j, album_data in enumerate(fetch_albums_data(batch_ids, headers)):
                    with open(albums_path / f"{batch_ids[j]}.json", "w") as f:
                        json.dump(album_data, f, indent=2)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching album data: {e}")

    print("all album data fetched")


def enrich_artists_data(artists_path, artist_ids, headers):
    """
    Fetch additional artist data from Spotify API and save as JSON files

    Args:
        artists_path: Path to save the artist JSON files
        artist_ids: List of artist IDs to fetch
        headers: Spotify API headers with authentication token
    """
    # Create output directory
    artists_path.mkdir(parents=True, exist_ok=True)

    # Filter out already cached artists
    uncached_artist_ids = [i for i in artist_ids if not (artists_path / f"{i}.json").exists()]

    # Process artists
    if uncached_artist_ids:
        for i in tqdm(range(0, len(uncached_artist_ids), 50), desc="Fetching artist data"):
            batch_ids = uncached_artist_ids[i : i + 50]
            try:
                for j, artist_data in enumerate(fetch_artists_data(batch_ids, headers)):
                    with open(artists_path / f"{batch_ids[j]}.json", "w") as f:
                        json.dump(artist_data, f, indent=2)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching artist data: {e}")

    print("all artist data fetched")


def save_tracks_parquet(input_parquet, tracks_path, output_parquet):
    """
    Create a parquet file from track JSON data and return album and artist IDs

    Args:
        tracks_path: Path to directory containing track JSON files
        output_parquet: Path to output parquet file

    Returns:
        tuple: (list of album IDs, list of artist IDs)
    """
    tracks_data = []
    album_ids = set()
    artist_ids = set()

    # Read all track JSON files
    for track_file in tqdm(list(tracks_path.glob("*.json")), desc="Processing tracks"):
        with open(track_file) as f:
            track = json.load(f)

            # Collect IDs
            album_ids.add(track["album"]["id"])
            for artist in track["artists"]:
                artist_ids.add(artist["id"])
            for artist in track["album"]["artists"]:
                artist_ids.add(artist["id"])

            track_data = {
                "track_id": track["id"],
                "track_name": track["name"],
                "track_duration_ms": track["duration_ms"],
                "track_explicit": track["explicit"],
                "track_popularity": track["popularity"],
                "track_number": track["track_number"],
                "disc_number": track["disc_number"],
                "album_id": track["album"]["id"],
                "main_artist_id": track["artists"][0]["id"],
                "artist_ids": ";".join([artist["id"] for artist in track["artists"]]),
            }
            tracks_data.append(track_data)

    # Create DataFrame, drop duplicates, and set data types
    df = pd.DataFrame(tracks_data)
    df = df.drop_duplicates()
    
    # Set data types
    df = df.astype({
        'track_id': 'string',
        'track_name': 'string',
        'track_duration_ms': 'int64',
        'track_explicit': 'bool',
        'track_popularity': 'int16',
        'track_number': 'int16',
        'disc_number': 'int16',
        'album_id': 'string',
        'main_artist_id': 'string',
        'artist_ids': 'string'
    })
    
    df.to_parquet(output_parquet, index=False)
    print(f"Created tracks parquet file at {output_parquet}")

    # Add album and artist IDs to listening history
    listening_history = pd.read_parquet(input_parquet)
    listening_history.merge(
        df[['track_id', 'main_artist_id', "album_id"]],
        on='track_id',
        how='left'
    ).to_parquet(data_dir / "listening_history.parquet", index=False)

    return list(album_ids), list(artist_ids)


def save_artists_parquet(artists_path, output_parquet):
    """
    Create a parquet file from artist JSON data

    Args:
        artists_path: Path to directory containing artist JSON files
        output_parquet: Path to output parquet file
    """
    artists_data = []

    # Read all artist JSON files
    for artist_file in tqdm(list(artists_path.glob("*.json")), desc="Processing artists"):
        with open(artist_file) as f:
            artist = json.load(f)
            # Create flattened artist data
            artist_data = {
                "artist_id": artist["id"],
                "artist_name": artist["name"],
                "artist_followers": artist["followers"]["total"],
                "artist_genres": ";".join(artist["genres"]) if artist["genres"] else "",
                "artist_popularity": artist["popularity"],
                "artist_image_url": artist["images"][0]["url"] if artist["images"] else "",
            }
            artists_data.append(artist_data)

    # Create DataFrame, drop duplicates, and save to parquet with specified dtypes
    df = pd.DataFrame(artists_data)
    df = df.drop_duplicates()
    
    # Set data types
    df = df.astype({
        'artist_id': 'string',
        'artist_name': 'string',
        'artist_followers': 'int32',
        'artist_genres': 'string',  # Store as semicolon-separated string
        'artist_popularity': 'int64',
        'artist_image_url': 'string'
    })
    
    df.to_parquet(output_parquet, index=False)
    print(f"Created artists parquet file at {output_parquet}")


def save_albums_parquet(albums_path, output_parquet):
    """
    Create a parquet file from album JSON data

    Args:
        albums_path: Path to directory containing album JSON files
        output_parquet: Path to output parquet file
    """
    albums_data = []

    # Read all album JSON files
    for album_file in tqdm(list(albums_path.glob("*.json")), desc="Processing albums"):
        with open(album_file) as f:
            album = json.load(f)
            album_data = {
                "album_id": album["id"],
                "album_name": album["name"],
                "album_type": album["album_type"],
                "album_total_tracks": album["total_tracks"],
                "album_release_date": album["release_date"],
                "album_release_date_precision": album["release_date_precision"],
                "album_label": album["label"],
                "album_popularity": album["popularity"],
                "album_artist_ids": ";".join([artist["id"] for artist in album["artists"]]),
                "album_track_ids": ";".join([track["id"] for track in album["tracks"]["items"]]),
                "album_image_url": album["images"][0]["url"] if album["images"] else "",
                "album_copyright_text": album["copyrights"][0]["text"] if album["copyrights"] else "",
                "album_copyright_type": album["copyrights"][0]["type"] if album["copyrights"] else "",
            }
            albums_data.append(album_data)

    # Create DataFrame, drop duplicates, and set data types
    df = pd.DataFrame(albums_data)
    df = df.drop_duplicates()

    df['album_release_year'] = pd.to_numeric(df['album_release_date'].str[:4], errors='coerce')
    df = df.drop(['album_release_date', 'album_release_date_precision'], axis=1)
    
    # Set data types
    df = df.astype({
        'album_id': 'string',
        'album_name': 'string',
        'album_type': 'string',
        'album_total_tracks': 'int16',
        'album_release_year': 'int16',
        'album_label': 'string',
        'album_popularity': 'int16',
        'album_artist_ids': 'string',
        'album_track_ids': 'string',
        'album_image_url': 'string',
        'album_copyright_text': 'string',
        'album_copyright_type': 'string'
    })
    
    df.to_parquet(output_parquet, index=False)
    print(f"Created albums parquet file at {output_parquet}")


if __name__ == "__main__":
    root_dir = Path(__file__).parent.parent
    data_dir = root_dir / "data"
    input_parquet = data_dir / "listening_history_without_ids.parquet"
    output_dir = data_dir / "spotify_data"
    tracks_path = output_dir / "tracks"
    albums_path = output_dir / "albums"
    artists_path = output_dir / "artists"

    # Use token from environment variable and validate it
    load_dotenv(root_dir / ".env", override=True)
    token = os.getenv("SPOTIFY_BEARER_TOKEN")
    if not token:
        raise ValueError("SPOTIFY_BEARER_TOKEN must be set in .env file")

    headers = {"Authorization": f"Bearer {token}"}
    
    # Process each data type
    enrich_tracks_data(input_parquet, tracks_path, headers)
    album_ids, artist_ids = save_tracks_parquet(input_parquet, tracks_path, data_dir / "tracks.parquet")

    enrich_albums_data(albums_path, album_ids, headers)
    save_artists_parquet(artists_path, data_dir / "artists.parquet")

    enrich_artists_data(artists_path, artist_ids, headers)
    save_albums_parquet(albums_path, data_dir / "albums.parquet")
