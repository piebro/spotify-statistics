import argparse
import os
import shutil
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


def extract_spotify_data(zip_path, raw_data_dir):
    # Create data/raw directory if it doesn't exist
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    # Open and extract zip file
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        # Get list of files in zip
        files = zip_ref.namelist()

        # Extract only files from "Spotify Extended Streaming History" folder
        for file in files:
            if "Spotify Extended Streaming History" in file:
                zip_ref.extract(file, raw_data_dir)

        # Move files from nested folder to raw directory
        source_dir = raw_data_dir / "Spotify Extended Streaming History"
        if source_dir.exists():
            for file in source_dir.glob("*"):
                shutil.move(str(file), str(raw_data_dir / file.name))
            # Remove empty directory
            source_dir.rmdir()


def read_json(path_or_buf):
    df = pd.read_json(
        path_or_buf,
        dtype={
            "ts": str,
            "track_id": "string",
            "platform": "string",
            "ms_played": np.int64,
            "conn_country": "string",
            "ip_addr_decrypted": "string",
            "master_metadata_track_name": "string",
            "master_metadata_album_artist_name": "string",
            "master_metadata_album_album_name": "string",
            "spotify_track_uri": "string",
            "episode_name": "string",
            "episode_show_name": "string",
            "spotify_episode_uri": "string",
            "reason_start": "string",
            "reason_end": "string",
            "shuffle": bool,
            "skipped": bool,
            "offline": bool,
            "offline_timestamp": np.int64,
            "incognito_mode": bool,
        },
    )
    df = df.rename(
        columns={
            "ip_addr_decrypted": "ip_addr",
            "master_metadata_track_name": "track",
            "master_metadata_album_artist_name": "artist",
            "master_metadata_album_album_name": "album",
        }
    )
    return df


def preprocess_df(df):
    df = df[df["track"] != "None"]
    df = df.drop_duplicates()

    df["ts"] = pd.to_datetime(df["ts"], format="%Y-%m-%dT%H:%M:%SZ")

    df.loc[df["offline_timestamp"] > 2000000000, "offline_timestamp"] /= (
        1000  # convert the data that is in ms to seconds
    )
    valid_offline_ts_mask = df["offline_timestamp"] > 100
    df["offline_timestamp"] = pd.to_datetime(df["offline_timestamp"], unit="s")
    df["ts"].values[valid_offline_ts_mask] = df.loc[valid_offline_ts_mask, "offline_timestamp"]

    df["reason_start"] = df["reason_start"].replace(
        {"backbtn": "back button", "fwdbtn": "forward button", "playbtn": "play button"}
    )
    df["reason_end"] = df["reason_end"].replace(
        {"backbtn": "back button", "endplay": "end play", "fwdbtn": "forward button"}
    )
    df["full_play"] = df["reason_end"] == "trackdone"
    df["track_id"] = df["spotify_track_uri"].str.split(":").str[-1].astype("string")

    df.sort_values(by="ts", ascending=True, inplace=True)

    df = df.drop(
        columns=[
            "ip_addr",
            "spotify_track_uri",
            "episode_name",
            "episode_show_name",
            "spotify_episode_uri",
            "offline_timestamp",
            "skipped",
        ]
    )
    # reorder df for a better overview
    df = df[
        [
            "track_id",
            "track",
            "artist",
            "album",
            "ts",
            "ms_played",
            "reason_start",
            "reason_end",
            "full_play",
            "conn_country",
            "platform",
            "shuffle",
            "offline",
            "incognito_mode",
        ]
    ]
    return df


def combine_and_save(input_dir, output_file):
    """
    Combine multiple Spotify JSON files into a single preprocessed parquet file

    Args:
        input_dir: Directory containing the JSON files
        output_file: Path to save the output parquet file
    """
    # Read and combine all JSON files
    df = pd.concat(
        [
            read_json(os.path.join(input_dir, fn))
            for fn in sorted(os.listdir(input_dir))
            if fn.endswith(".json")
        ]
    )

    # Preprocess the data
    df = preprocess_df(df)

    # Save to parquet
    df.to_parquet(output_file, index=False)
    print(f"Saved combined data to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract Spotify streaming history from data download zip file"
    )
    parser.add_argument("zip_path", type=str, help="Path to the Spotify data zip file")
    args = parser.parse_args()

    raw_data_dir = Path("data/raw")
    output_file = Path("data/listening_history_without_ids.parquet")

    extract_spotify_data(args.zip_path, raw_data_dir)
    combine_and_save(raw_data_dir, output_file)
