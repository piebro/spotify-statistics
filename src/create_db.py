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
            "platform": str,
            "ms_played": np.int64,
            "conn_country": str,
            "ip_addr_decrypted": str,
            "master_metadata_track_name": str,
            "master_metadata_album_artist_name": str,
            "master_metadata_album_album_name": str,
            "spotify_track_uri": str,
            "episode_name": str,
            "episode_show_name": str,
            "spotify_episode_uri": str,
            "reason_start": str,
            "reason_end": str,
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

    df["year_month"] = df["ts"].dt.to_period("M")
    df["year"] = df["ts"].dt.year
    df["month"] = df["ts"].dt.month

    earliest_month = df["year_month"].min()
    df["month_index"] = (df["year_month"] - earliest_month).apply(lambda x: x.n)
    df["year_month"] = df["year_month"].dt.strftime("%Y-%m")

    df["year_month_day"] = df["ts"].dt.strftime("%Y-%m-%d")
    df["day_name"] = df["ts"].dt.day_name().astype(str)

    df["minutes_played"] = df["ms_played"] / 1000 / 60
    df["hours_played"] = df["ms_played"] / 1000 / 60 / 60

    df["reason_start"] = df["reason_start"].replace(
        {"backbtn": "back button", "fwdbtn": "forward button", "playbtn": "play button"}
    )
    df["reason_end"] = df["reason_end"].replace(
        {"backbtn": "back button", "endplay": "end play", "fwdbtn": "forward button"}
    )

    df["full_play"] = df["reason_end"] == "trackdone"

    df["track"] = df["track"] + "~~sep~~" + df["artist"]
    df["album"] = df["album"] + "~~sep~~" + df["artist"]

    df["track_id"] = df["spotify_track_uri"].str.split(":").str[-1]

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
            "track",
            "artist",
            "album",
            "year_month_day",
            "day_name",
            "minutes_played",
            "reason_start",
            "reason_end",
            "conn_country",
            "platform",
            "shuffle",
            "full_play",
            "offline",
            "incognito_mode",
            "ts",
            "year",
            "year_month",
            "month",
            "month_index",
            "ms_played",
            "hours_played",
            "track_id",
        ]
    ]
    return df


def combine_to_csv(input_dir, output_file):
    """
    Combine multiple Spotify JSON files into a single preprocessed CSV file

    Args:
        input_dir: Directory containing the JSON files
        output_file: Path to save the output CSV file
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

    # Convert timestamp to string format before saving
    df["ts"] = df["ts"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Save to CSV
    df.to_csv(output_file, index=False)
    print(f"Saved combined data to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract Spotify streaming history from data download zip file"
    )
    parser.add_argument("zip_path", type=str, help="Path to the Spotify data zip file")
    args = parser.parse_args()

    raw_data_dir = Path("data/raw")
    output_file = Path("data/listening_history.csv")

    extract_spotify_data(args.zip_path, raw_data_dir)
    combine_to_csv(raw_data_dir, output_file)
