import argparse
import json
import time
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

from util import get_spotify_bearer


def fetch_data(url, headers, params=None):
    """Fetch data from Spotify API"""
    response = requests.get(url, headers=headers, params=params)
    time.sleep(0.1)

    if response.status_code == 429:  # Rate limit exceeded
        retry_after = int(response.headers.get("Retry-After", 1))
        time.sleep(retry_after)
        return fetch_data(url, headers, params)

    if response.status_code == 401:  # Invalid token
        raise ValueError("Invalid or expired Spotify token. Please refresh your token.")

    response.raise_for_status()
    return response.json()


def download_image(url, output_path):
    try:
        image_response = requests.get(url)
        image_response.raise_for_status()
        with open(output_path, "wb") as img_file:
            img_file.write(image_response.content)
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
        return False


def save_raw_tracks_data(input_parquet, tracks_path, headers):
    tracks_path.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(input_parquet)
    track_ids = df["track_id"].unique().tolist()
    uncached_track_ids = [i for i in track_ids if not (tracks_path / f"{i}.json").exists()]

    # Process tracks
    if uncached_track_ids:
        url = "https://api.spotify.com/v1/tracks"
        for i in tqdm(range(0, len(uncached_track_ids), 50), desc="Fetching track data"):
            batch_ids = uncached_track_ids[i : i + 50]
            try:
                params = {"ids": ",".join(batch_ids)}
                response = fetch_data(url, headers, params)
                for j, track_data in enumerate(response["tracks"]):
                    with open(tracks_path / f"{batch_ids[j]}.json", "w") as f:
                        json.dump(track_data, f, indent=2)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching track data: {e}")

    print("all track data fetched")


def save_tracks_parquet(input_parquet, tracks_path, output_parquet):
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
                "artist_id": track["artists"][0]["id"],
                "artist_ids": ";".join([artist["id"] for artist in track["artists"]]),
            }
            tracks_data.append(track_data)

    # Create DataFrame, drop duplicates, and set data types
    df = pd.DataFrame(tracks_data)
    df = df.drop_duplicates()

    # Set data types
    df = df.astype(
        {
            "track_id": "string",
            "track_name": "string",
            "track_duration_ms": "Int64",
            "track_explicit": "bool",
            "track_popularity": "Int16",
            "track_number": "Int16",
            "disc_number": "Int16",
            "album_id": "string",
            "artist_id": "string",
            "artist_ids": "string",
        }
    )

    # Add album and artist IDs to listening history
    listening_history = pd.read_parquet(input_parquet)
    listening_history.merge(df[["track_id", "artist_id"]], on="track_id", how="left")[
        ["track_id", "artist_id"] + [col for col in listening_history.columns if col != "track_id"]
    ].to_parquet(data_dir / "listening_history.parquet", index=False)

    df = df.drop(columns=["artist_id"])
    df.to_parquet(output_parquet, index=False)
    print(f"Created tracks parquet file at {output_parquet}")

    return list(album_ids), list(artist_ids)


def save_raw_artists_data(artists_path, artist_ids, headers):
    artists_path.mkdir(parents=True, exist_ok=True)
    # Create images directory
    images_path = artists_path.parent / "artist_images"
    images_path.mkdir(parents=True, exist_ok=True)

    uncached_artist_ids = [i for i in artist_ids if not (artists_path / f"{i}.json").exists()]

    # Process artists
    if uncached_artist_ids:
        url = "https://api.spotify.com/v1/artists"
        for i in tqdm(range(0, len(uncached_artist_ids), 50), desc="Fetching artist data"):
            batch_ids = uncached_artist_ids[i : i + 50]
            try:
                response = fetch_data(url, headers, {"ids": ",".join(batch_ids)})
                for j, artist_data in enumerate(response["artists"]):
                    with open(artists_path / f"{batch_ids[j]}.json", "w") as f:
                        json.dump(artist_data, f, indent=2)

            except requests.exceptions.RequestException as e:
                print(f"Error fetching artist data: {e}")

    print("all artist data and images fetched")


def save_raw_artist_top_tracks(top_tracks_path, artist_ids, headers):
    top_tracks_path.mkdir(parents=True, exist_ok=True)
    uncached_artist_ids = [i for i in artist_ids if not (top_tracks_path / f"{i}_top_tracks.json").exists()]

    # Process artists' top tracks
    if uncached_artist_ids:
        for artist_id in tqdm(uncached_artist_ids, desc="Fetching artist top tracks"):
            try:
                url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
                response = fetch_data(url, headers)
                with open(top_tracks_path / f"{artist_id}_top_tracks.json", "w") as f:
                    json.dump(response["tracks"], f, indent=2)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching top tracks for artist {artist_id}: {e}")

    print("all artist top tracks fetched")


def download_artist_images(artists_path, images_path):
    """Download images for all artists in the artists directory."""
    images_path.mkdir(parents=True, exist_ok=True)

    ids_to_process = [
        f.stem for f in artists_path.glob("*.json") if not (images_path / f"{f.stem}.jpg").exists()
    ]
    for artist_id in tqdm(ids_to_process, desc="Downloading artist images"):
        image_path = images_path / f"{artist_id}.jpg"

        with open(artists_path / f"{artist_id}.json") as f:
            artist_data = json.load(f)
            if artist_data["images"] and artist_data["images"][0]["url"]:
                image_url = artist_data["images"][0]["url"]
                if not download_image(image_url, image_path):
                    print(f"Failed to download image for artist {artist_id}")

    print("All artist images downloaded")


def fetch_artist_wikidata(spotify_id):
    """Fetch Wikidata information for an artist using their Spotify ID."""
    endpoint_url = "https://query.wikidata.org/sparql"

    query = f"""
    SELECT ?item ?propLabel ?valueLabel WHERE {{
      ?item wdt:P1902 "{spotify_id}".
      ?item ?prop ?value .
      ?property wikibase:directClaim ?prop .
      SERVICE wikibase:label {{ 
        bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en".
        ?property rdfs:label ?propLabel .
        ?value rdfs:label ?valueLabel .
      }}
    }}
    """

    try:
        response = requests.get(
            endpoint_url,
            params={"query": query, "format": "json"},
            headers={"User-Agent": "MusicDataAnalysis/1.0"},
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Wikidata for Spotify ID {spotify_id}: {e}")
        return None


def save_artist_wikidata(artists_path, wikidata_path):
    """Download Wikidata for all artists and save as JSON files."""
    wikidata_path.mkdir(parents=True, exist_ok=True)

    # Process only artists that don't have wikidata yet
    for artist_file in tqdm(list(artists_path.glob("*.json")), desc="Fetching Wikidata"):
        wikidata_file = wikidata_path / f"{artist_file.stem}.json"

        if not wikidata_file.exists():
            artist_id = artist_file.stem  # This is the Spotify ID
            time.sleep(0.01)  # Rate limiting
            wikidata = fetch_artist_wikidata(artist_id)

            # Save either the wikidata or an empty dict if no data was found
            with open(wikidata_file, "w") as f:
                json.dump(wikidata if wikidata else {}, f, indent=2)

    print("All artist Wikidata fetched")


def save_artists_parquet(artists_path, top_tracks_path, wikidata_path, output_parquet):
    artists_data = []
    # Read all artist JSON files
    for artist_file in tqdm(list(artists_path.glob("*.json")), desc="Processing artists"):
        with open(artist_file) as f:
            artist = json.load(f)

            # Try to load top tracks data
            # top_tracks_file = top_tracks_path / f"{artist['id']}_top_tracks.json"
            # top_track_ids = []
            # if top_tracks_file.exists():
            #     with open(top_tracks_file) as tf:
            #         top_tracks = json.load(tf)
            #         top_track_ids = [track["id"] for track in top_tracks]

            # Load Wikidata
            wikidata_file = wikidata_path / f"{artist['id']}.json"
            wikidata_entity_id = None
            gender = None
            citizenship_or_country_of_origin = None
            birth_date = None
            website = None
            is_band = None
            all_genres = set(artist["genres"] if artist["genres"] else [])  # Start with Spotify genres

            if wikidata_file.exists():
                with open(wikidata_file) as wf:
                    wikidata = json.load(wf)

                    if wikidata != {} and len(wikidata["results"]["bindings"]) > 0:
                        wikidata_entity_id = wikidata["results"]["bindings"][0]["item"]["value"].split("/")[-1]
                        for binding in wikidata["results"]["bindings"]:
                            prop_label = binding["propLabel"]["value"].lower()
                            value_label = binding["valueLabel"]["value"]
                            if prop_label == "instance of":
                                if value_label in ["human", "solo musical project"]:
                                    is_band = False
                                elif value_label in [
                                    "musical group",
                                    "musical duo",
                                    "rock band",
                                    "orchestra",
                                    "symphony orchestra",
                                    "sibling duo",
                                    "musical trio",
                                    "girl group",
                                    "musical ensemble",
                                    "rap group",
                                ]:
                                    is_band = True
                            elif prop_label == "sex or gender":
                                gender = value_label
                            elif prop_label in ["country of citizenship", "country of origin"]:
                                citizenship_or_country_of_origin = value_label
                            elif prop_label == "date of birth":
                                birth_date = value_label
                            elif prop_label == "official website":
                                website = value_label
                            elif prop_label == "genre":
                                all_genres.add(value_label)

            # Create flattened artist data
            artist_data = {
                "artist_id": artist["id"],
                "artist_name": artist["name"],
                "artist_followers": artist["followers"]["total"],
                "artist_genres": ";".join(sorted(all_genres)) if all_genres else "",
                "artist_popularity": artist["popularity"],
                # "top_track_ids": ";".join(top_track_ids),
                "wikidata_entity_id": wikidata_entity_id,
                "is_band": is_band,
                "gender": gender,
                "country": citizenship_or_country_of_origin,
                "birth_date": birth_date,
                "website": website,
            }
            artists_data.append(artist_data)

    # Create DataFrame, drop duplicates, and save to parquet with specified dtypes
    df = pd.DataFrame(artists_data)
    df = df.drop_duplicates()

    # Convert birth_date to datetime
    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")

    # Set data types
    df = df.astype(
        {
            "artist_id": "string",
            "artist_name": "string",
            "artist_followers": "Int32",
            "artist_genres": "string",
            "artist_popularity": "Int64",
            # "top_track_ids": "string",
            "wikidata_entity_id": "string",
            "is_band": "boolean",
            "gender": "string",
            "country": "string",
            "website": "string",
        }
    )

    df.to_parquet(output_parquet, index=False)
    print(f"Created artists parquet file at {output_parquet}")


def save_raw_albums_data(albums_path, album_ids, headers):
    albums_path.mkdir(parents=True, exist_ok=True)
    uncached_album_ids = [i for i in album_ids if not (albums_path / f"{i}.json").exists()]

    # Process albums
    if uncached_album_ids:
        url = "https://api.spotify.com/v1/albums"
        for i in tqdm(range(0, len(uncached_album_ids), 20), desc="Fetching album data"):
            batch_ids = uncached_album_ids[i : i + 20]
            try:
                response = fetch_data(url, headers, {"ids": ",".join(batch_ids)})
                for j, album_data in enumerate(response["albums"]):
                    with open(albums_path / f"{batch_ids[j]}.json", "w") as f:
                        json.dump(album_data, f, indent=2)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching album data: {e}")

    print("all album data fetched")


def save_albums_parquet(albums_path, output_parquet):
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
            }
            albums_data.append(album_data)

    # Create DataFrame, drop duplicates, and set data types
    df = pd.DataFrame(albums_data)
    df = df.drop_duplicates()

    df["album_release_date"] = df["album_release_date"].replace({"1900-01-01": "0"})
    df["album_release_year"] = pd.to_numeric(df["album_release_date"].str[:4], errors="coerce")
    df = df.drop(["album_release_date", "album_release_date_precision"], axis=1)

    # Set data types
    df = df.astype(
        {
            "album_id": "string",
            "album_name": "string",
            "album_type": "string",
            "album_total_tracks": "Int16",
            "album_release_year": "Int16",
            "album_label": "string",
            "album_popularity": "Int16",
            "album_artist_ids": "string",
            "album_track_ids": "string",
        }
    )

    df.to_parquet(output_parquet, index=False)
    print(f"Created albums parquet file at {output_parquet}")


def download_album_images(albums_path, images_path):
    """Download images for all albums in the albums directory."""
    images_path.mkdir(parents=True, exist_ok=True)

    ids_to_process = [
        f.stem for f in albums_path.glob("*.json") if not (images_path / f"{f.stem}.jpg").exists()
    ]
    for album_id in tqdm(ids_to_process, desc="Downloading album images"):
        image_path = images_path / f"{album_id}.jpg"

        with open(albums_path / f"{album_id}.json") as f:
            album_data = json.load(f)
            if album_data["images"] and album_data["images"][0]["url"]:
                image_url = album_data["images"][0]["url"]
                if not download_image(image_url, image_path):
                    print(f"Failed to download image for album {album_id}")

    print("All album images downloaded")


def save_listening_history_with_internet_data(data_dir, output_parquet):
    df_tracks = pd.read_parquet(data_dir / "tracks.parquet")
    df_albums = pd.read_parquet(data_dir / "albums.parquet")
    df_artists = pd.read_parquet(data_dir / "artists.parquet")
    df_history = pd.read_parquet(data_dir / "listening_history.parquet")
    df_all = (
        df_history
            .merge(df_tracks, on='track_id', how='left')
            .merge(df_albums, on='album_id', how='left')
            .merge(df_artists, on='artist_id', how='left')
    )
    df_all["hours_played"] = df_all["ms_played"] / (1000 * 60 * 60)
    df_all.to_parquet(output_parquet, index=False)
    print(f"Created listening history with internet data parquet file at {output_parquet}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Spotify data")
    parser.add_argument(
        "--fetch-top-tracks",
        action="store_true",
        help="Fetch artist top tracks data (slower, but provides additional data)",
    )
    args = parser.parse_args()

    root_dir = Path(__file__).parent.parent
    data_dir = root_dir / "data"
    input_parquet = data_dir / "listening_history_without_ids.parquet"
    spotify_data_dir = data_dir / "spotify_data"
    tracks_path = spotify_data_dir / "tracks"
    albums_path = spotify_data_dir / "albums"
    artists_path = spotify_data_dir / "artists"
    top_tracks_path = spotify_data_dir / "top_tracks"

    token = get_spotify_bearer()
    headers = {"Authorization": f"Bearer {token}"}

    save_raw_tracks_data(input_parquet, tracks_path, headers)
    album_ids, artist_ids = save_tracks_parquet(input_parquet, tracks_path, data_dir / "tracks.parquet")

    save_raw_artists_data(artists_path, artist_ids, headers)
    if args.fetch_top_tracks:
        save_raw_artist_top_tracks(top_tracks_path, artist_ids, headers)
    save_artist_wikidata(artists_path, data_dir / "artist_wikidata")
    save_artists_parquet(
        artists_path, top_tracks_path, data_dir / "artist_wikidata", data_dir / "artists.parquet"
    )
    # download_artist_images(artists_path, data_dir / "artist_images")

    save_raw_albums_data(albums_path, album_ids, headers)
    save_albums_parquet(albums_path, data_dir / "albums.parquet")
    # download_album_images(albums_path, data_dir / "album_images")

    save_listening_history_with_internet_data(data_dir, data_dir / "listening_history_with_internet_data.parquet")