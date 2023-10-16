import os
import sys
import json
import base64
from io import BytesIO

import numpy as np
import pandas as pd


def read_json(path_or_buf):
    df = pd.read_json(
        path_or_buf,
        dtype={
            "ts": str,
            "username": str,
            "platform": str,
            "ms_played": np.int64,
            "conn_country": str,
            "ip_addr_decrypted": str,
            "user_agent_decrypted": str,
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
            "user_agent_decrypted": "user_agent",
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
    df.loc[df["offline_timestamp"] > 2000000000, "offline_timestamp"] /= 1000
    mask = df["offline_timestamp"] > 100
    df["offline_timestamp"] = pd.to_datetime(df["offline_timestamp"], unit="s")
    df["ts"].values[mask] = df.loc[mask, "offline_timestamp"]

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

    df["reason_start"].replace(
        {"backbtn": "back button", "fwdbtn": "forward button", "playbtn": "play button"}, inplace=True
    )
    df["reason_end"].replace(
        {"backbtn": "back button", "endplay": "end play", "fwdbtn": "forward button"}, inplace=True
    )

    df["full_play"] = df["reason_end"] == "trackdone"

    df["track"] = df["track"] + "~~sep~~" + df["artist"]
    df["album"] = df["album"] + "~~sep~~" + df["artist"]

    df.sort_values(by="ts", ascending=True, inplace=True)

    df = df.drop(
        columns=[
            "user_agent",
            "username",
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
        ]
    ]
    return df


def df_dict_to_df_json_dict(df_dict):
    for name, df in df_dict.items():
        df = df.round(2)
        df_dict[name] = df.to_dict(orient="split")
        del df_dict[name]["index"]


def save_dataframe_dict(df_dict):
    os.makedirs(os.path.join("assets", "data"), exist_ok=True)
    for name, df in df_dict.items():
        df.to_json(
            os.path.join("assets", "data", f"{name}.json"), orient="split", index=False, indent=0, double_precision=2
        )


def save_json(data_name, data):
    os.makedirs(os.path.join("assets", "data"), exist_ok=True)
    with open(os.path.join("assets", "data", f"{data_name}.json"), "w") as f:
        json.dump(data, f, indent=2)


def replace_track_artist(df):
    """Split the track into track name and artist and insert artist as a new column."""
    column_index = df.columns.get_loc("track")
    split_track_artist = df["track"].str.split("~~sep~~", n=1, expand=True)
    df["track"] = split_track_artist[0]
    if "artist" not in df:
        df.insert(column_index + 1, "artist", split_track_artist[1])


def replace_album_artist(df):
    """Split the album into album name and artist and insert artist as a new column."""
    column_index = df.columns.get_loc("album")
    split_track_artist = df["album"].str.split("~~sep~~", n=1, expand=True)
    df["album"] = split_track_artist[0]
    if "artist" not in df:
        df.insert(column_index + 1, "artist", split_track_artist[1])


def country_code_to_country_name(df):
    df["conn_country"] = df["conn_country"].apply(
        lambda x: country_code_to_name[x] if x in country_code_to_name else "unknown"
    )


def post_process_dataframe_dict(df_dict):
    for _, df in df_dict.items():
        if "track" in df:
            replace_track_artist(df)
        if "album" in df:
            replace_album_artist(df)
        if "hours_played" in df:
            df.rename(columns={"hours_played": "hours played"}, inplace=True)
        if "conn_country" in df:
            country_code_to_country_name(df)
        if "year_month" in df:
            df.rename(columns={"year_month": "month"}, inplace=True)


def numpy_to_base64_bmp(array):
    array = np.flipud(array)  # Flip the array vertically
    padding = b"\x00" * ((4 - (array.shape[1] % 4)) % 4)  # Calculate row padding
    output = BytesIO()

    # BMP file header
    output.write(b"BM")  # ID field
    output.write(
        (array.size + len(padding) * array.shape[0] + 1078).to_bytes(4, "little")
    )  # the size of the BMP file in bytes
    output.write((0).to_bytes(4, "little"))  # reserved
    output.write((1078).to_bytes(4, "little"))  # the offset where the pixel array (bitmap data) can be found

    # DIB header
    output.write((40).to_bytes(4, "little"))  # the size of this header (40 bytes)
    output.write((array.shape[1]).to_bytes(4, "little"))  # the bitmap width in pixels
    output.write((array.shape[0]).to_bytes(4, "little"))  # the bitmap height in pixels
    output.write((1).to_bytes(2, "little"))  # the number of color planes
    output.write((8).to_bytes(2, "little"))  # the number of bits per pixel
    output.write((0).to_bytes(4, "little"))  # the compression method
    output.write((array.size + len(padding) * array.shape[0]).to_bytes(4, "little"))  # the image size
    output.write((0).to_bytes(4, "little"))  # the horizontal resolution
    output.write((0).to_bytes(4, "little"))  # the vertical resolution
    output.write((256).to_bytes(4, "little"))  # the number of colors in the color palette
    output.write((0).to_bytes(4, "little"))  # the number of important colors used

    # color palette
    for i in range(256):
        output.write(bytes([i, i, i, 0]))

    # pixel array
    for row in array:
        output.write(row.tobytes())
        output.write(padding)  # Add row padding

    # Get the byte data
    byte_data = output.getvalue()

    # Convert the bytes to base64 string
    base64_str = base64.b64encode(byte_data).decode("utf-8")

    return base64_str


def get_monthly_play_images(df, column_name):
    """Create images representing the monthly play count for each unique value in the specified column."""
    image_width = df["month_index"].max() + 1

    name_groups = df.groupby([column_name, "month_index"]).size().rename("count").reset_index().groupby(column_name)

    grouped = df.groupby([column_name, "month_index"]).size().rename("count").reset_index()
    name_groups = grouped.groupby(column_name)

    all_values = grouped["count"].values
    y_value_multiplier = 40 / np.percentile(all_values, 99)

    names = []
    images = []
    for name, group in name_groups:
        names.append(name)

        image = np.ones((image_width, 40), dtype=np.uint8) * 210
        for index, value in zip(group["month_index"], group["count"]):
            image[index, 40 - min(int(np.round(value * y_value_multiplier)), 40) :] = 0

        images.append(f"data:image/bmp;base64,{numpy_to_base64_bmp(image.T)}")

    df = pd.DataFrame({column_name: names, f"monthly play count<br>(up to {int(40/y_value_multiplier)} plays)": images})
    return df


def get_most_played_artists_tracks_albums_total(
    df, top_k, suffix="", column_name_muliplier_list=("artist", "track", "album")
):
    """Save the top k artists, tracks, and albums with the most plays."""
    df_dict = {}
    for column_name in column_name_muliplier_list:
        df_top = df.groupby([column_name]).agg({"full_play": "sum", "hours_played": "sum"})
        df_top.rename(columns={"full_play": "play count"}, inplace=True)
        df_top = df_top.reset_index().nlargest(top_k, "play count")

        if column_name == "artist":
            artist_track_count = df.groupby("artist")["track"].nunique().to_dict()
            df_top["# of unique tracks played"] = df_top["artist"].map(artist_track_count)

        df_image = get_monthly_play_images(
            df[(df[column_name].isin(df_top[column_name])) & df["full_play"]], column_name
        )
        df_top = pd.merge(df_top, df_image, on=column_name)
        df_dict[f"most_played_{column_name}s_total{suffix}"] = df_top
    return df_dict


def get_top_songs_of_top_artists(df, top_k):
    """Get the top 3 songs of the top k artists sorted by playcount."""

    # Group by artist to get the top k artists by play count
    top_artists_data = df.groupby("artist").agg({"full_play": "sum"}).nlargest(top_k, "full_play")

    artists = []
    top_1_songs = []
    top_2_songs = []
    top_3_songs = []
    for artist, play_count in top_artists_data.iterrows():
        artist_data = df[df["artist"] == artist]

        # Group by track and aggregate the sum of plays to get top 3 songs
        top_tracks = artist_data.groupby("track").agg({"full_play": "sum"}).nlargest(3, "full_play")

        artists.append(f"{artist} ({play_count['full_play']} plays)")
        top_1_songs.append(f"{top_tracks.index[0].split('~~sep~~')[0]} ({top_tracks.iloc[0, 0]} plays)")

        if len(top_tracks) > 1:
            top_2_songs.append(f"{top_tracks.index[1].split('~~sep~~')[0]} ({top_tracks.iloc[1, 0]} plays)")
        else:
            top_2_songs.append(None)

        if len(top_tracks) > 2:
            top_3_songs.append(f"{top_tracks.index[2].split('~~sep~~')[0]} ({top_tracks.iloc[2, 0]} plays)")
        else:
            top_3_songs.append(None)

    result_df = pd.DataFrame(
        {"artist": artists, "top-1 song": top_1_songs, "top-2 song": top_2_songs, "top-3 song": top_3_songs}
    )
    return {"top_songs_of_top_artists": result_df}


def get_most_played_artist_track_album_monthly(df):
    """Save the artist, track, and album with the most plays for each month."""
    combined_df = df[["year_month"]].drop_duplicates().sort_values(by="year_month").reset_index(drop=True)
    for column_name in ["artist", "track", "album"]:
        df_top = (
            df.groupby(["year_month", column_name])
            .size()
            .reset_index(name="play count")
            .loc[lambda x: x.groupby("year_month")["play count"].idxmax()]
        )

        if column_name in ["track", "album"]:
            df_top[column_name] = df_top[column_name].str.replace("~~sep~~", " (by ")
            seperator = ", "
        else:
            seperator = " ("
        df_top[f"most played {column_name}"] = (
            df_top[column_name] + seperator + df_top["play count"].astype(str) + " times)"
        )

        combined_df = pd.merge(
            combined_df, df_top[["year_month", f"most played {column_name}"]], on="year_month", how="left"
        )

    combined_df = combined_df.sort_values(by="year_month", ascending=False).reset_index(drop=True)
    return {"most_played_artists_track_album_monthly": combined_df}


def get_avg_track_length_monthly(df):
    """Save the average track length for each month."""
    df = (
        df[df["full_play"]]
        .groupby("year_month")["minutes_played"]
        .agg(lambda series: series.sum() / series.size)
        .reset_index()
        .rename(columns={"minutes_played": "minutes played"})
    )
    return {"avg_track_length_monthly": df}


def get_avg_play_count_per_song_yearly(df):
    """Get the average play count for unique songs for each year."""

    # Calculate play count for each unique song in each year
    play_counts = df[df["full_play"]].groupby(["year", "track"]).size().reset_index(name="play count")

    # Calculate average play count for each year
    avg_play_counts = play_counts.groupby("year")["play count"].mean().reset_index()

    return {"avg_play_count_per_song_yearly": avg_play_counts}


def get_play_count_distribution(df):
    """Get the distribution of play counts for unique songs across all years."""

    # Calculate play count for each unique song across all years
    play_counts = df[df["full_play"]].groupby(["track"]).size().reset_index(name="play count")

    # Get distribution of play counts
    distribution = play_counts.groupby("play count").size().reset_index(name="num of songs")
    distribution = distribution.sort_values(by="play count", ascending=False)

    return {"play_count_distribution": distribution}


def get_yeary_track_artist_play_count(df):
    """Get monthly play count for tracks and number of unique tracks played."""
    out = {}

    play_counts = df[df["full_play"]].groupby(["year"])["track"].size().reset_index(name="total")
    unique = df[df["full_play"]].groupby("year")["track"].nunique().reset_index(name="unique per year")

    df_sorted = df[df["full_play"]].sort_values("year")
    seen_tracks = set()

    def mark_new_tracks(row):
        if row["track"] in seen_tracks:
            return False
        else:
            seen_tracks.add(row["track"])
            return True

    df_sorted["is_new"] = df_sorted.apply(mark_new_tracks, axis=1)
    new_tracks = df_sorted[df_sorted["is_new"]].groupby("year").size().reset_index(name="new")

    result = pd.merge(play_counts, unique, on="year", how="left")
    result = pd.merge(result, new_tracks, on="year", how="left").fillna(0)
    out["yearly_track_play_count"] = result
    return out


def get_hours_played_per_hour_of_the_day(df):
    df["hour"] = df["ts"].dt.hour
    hours_per_period = df.groupby(["hour"])["hours_played"].sum().reset_index()

    hours_per_period["hours_played"] = np.round(
        hours_per_period["hours_played"] / hours_per_period["hours_played"].sum() * 100, 2
    )
    hours_per_period = hours_per_period.rename(
        columns={"hour": "hour of the day", "hours_played": "percent of play time"}
    )

    return {"hours_played_percent_per_hour_of_the_day": hours_per_period}


def get_avg_hours_played_per_year_month_weekday(df):
    df_dict = {}

    # Get the first and last day in the dataset
    first_day = pd.Timestamp(df["year_month_day"].min())
    last_day = pd.Timestamp(df["year_month_day"].max())

    for time_period in ["year_month", "year", "month", "day_name"]:
        hours_per_period = df.groupby([time_period])["hours_played"].sum()

        if time_period == "year_month":
            # Calculate the number of days in each month between the first and last logged days
            days_per_period = pd.date_range(start=first_day, end=last_day).to_period("M").value_counts().sort_index()
            days_per_period.index = days_per_period.index.strftime("%Y-%m")

        elif time_period == "year":
            # Calculate the number of days in each year, using the actual start and end days in the first and last years
            days_per_period = pd.Series(index=hours_per_period.index, data=365)
            days_per_period[first_day.year] = (pd.Timestamp(f"{first_day.year}-12-31") - first_day).days + 1
            days_per_period[last_day.year] = (last_day - pd.Timestamp(f"{last_day.year}-01-01")).days + 1

        elif time_period == "month":
            month_names = [pd.Timestamp(2023, x, 1).month_name() for x in range(1, 13)]

            hours_per_period.index = pd.Series(hours_per_period.index).apply(lambda x: month_names[x - 1])
            hours_per_period.index = pd.CategoricalIndex(hours_per_period.index, categories=month_names, ordered=True)
            hours_per_period.sort_index(inplace=True)

            df_data_range = pd.DataFrame(pd.date_range(first_day, last_day), columns=["date"])
            df_data_range["month"] = df_data_range["date"].dt.month_name()
            days_per_period = df_data_range.groupby(["month"]).size()
            days_per_period.index = pd.CategoricalIndex(days_per_period.index, categories=month_names, ordered=True)
            days_per_period.sort_index(inplace=True)

        elif time_period == "day_name":
            # Calculate the number of each weekday between the first and last logged days
            days_per_period = pd.date_range(start=first_day, end=last_day).day_name().value_counts().sort_index()

            # Sort weekdays from Monday to Sunday
            weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            hours_per_period.index = pd.Categorical(hours_per_period.index, categories=weekdays, ordered=True)
            hours_per_period = hours_per_period.sort_index()
            days_per_period.index = pd.Categorical(days_per_period.index, categories=weekdays, ordered=True)
            days_per_period = days_per_period.sort_index()

        avg_hours_per_period = hours_per_period / days_per_period

        avg_hours_per_period = (
            avg_hours_per_period.rename("avg hours played per day")
            .reset_index()
            .rename(columns={"index": time_period.replace("_", " ")})
        )

        df_dict[f"avg_hours_played_per_{time_period}"] = avg_hours_per_period
    return df_dict


def get_plays_per_county_toal(df):
    df = (
        df[df["full_play"]]
        .groupby("conn_country")
        .size()
        .rename("full_playes")
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"conn_country": "country", "full_playes": "play count"})
    )
    return {"plays_per_county_total": df}


def get_cumulative_percent_play_count_track_artists(df):
    out = {}
    for unit in ("track", "artist"):
        count_per_unit = (
            df[df["full_play"]]
            .groupby(unit)
            .size()
            .reset_index(name="played count")
            .sort_values(by="played count", ascending=False)
        )
        count_per_unit[f"number of {unit}s"] = range(1, len(count_per_unit) + 1)

        # Calculate the percentage of the cumulative sum
        total_played_songs = len(df[df["full_play"]])
        count_per_unit["percent of played songs"] = (count_per_unit["played count"].cumsum() / total_played_songs) * 100

        count_per_unit = count_per_unit.drop(columns=[unit, "played count"])

        count_per_unit = pd.concat(
            [pd.DataFrame({f"number of {unit}s": [0], "percent of played songs": [0]}), count_per_unit]
        )
        out[f"cumulative_percent_play_count_{unit}"] = count_per_unit

    return out


def hours_to_str(hours):
    if hours >= 10:
        return f"{round(hours)}h"
    else:
        return f"{int(hours)}:{str(round((hours % 1) * 60)).zfill(2)}h"


def get_single_values(df, df_dict):
    data = {}
    data["first_day"] = df["year_month_day"].min()
    data["last_day"] = df["year_month_day"].max()
    first_day_ts = pd.Timestamp(data["first_day"])
    last_day_ts = pd.Timestamp(data["last_day"])
    data["number_of_days"] = (last_day_ts - first_day_ts).days
    data["number_of_days_with_tracks_played"] = df[df["full_play"]]["year_month_day"].nunique()
    data["percent_of_days_with_tracks_played"] = round(
        data["number_of_days_with_tracks_played"] / data["number_of_days"] * 100
    )

    df_full_play = df[df["full_play"]]

    played_songs = len(df_full_play)
    data["played_songs"] = played_songs
    data["played_songs_per_day"] = round(played_songs / data["number_of_days"])

    data["unique_tracks_played"] = df_full_play["track"].nunique()
    data["unique_artists_played"] = df_full_play["artist"].nunique()
    data["unique_albums_played"] = df_full_play["album"].nunique()
    data["unique_tracks_played_per_artist"] = round(data["unique_tracks_played"] / data["unique_artists_played"], 1)

    data["listening_hours"] = round(df["hours_played"].sum())
    data["listening_hours_per_day"] = hours_to_str(data["listening_hours"] / data["number_of_days"])[:-1]

    played_shuffle_count = len(df_full_play[df_full_play["shuffle"]])
    data["percent_of_played_songs_using_shuffle"] = round(played_shuffle_count / played_songs * 100)

    started_songs_shuffle = len(df[df["shuffle"]])
    skipped_df = df[df["reason_end"] == "forward button"]
    skipped_songs = len(skipped_df)
    data["skipped_songs"] = skipped_songs
    data["percent_of_skipped_songs"] = round(skipped_songs / (len(df)) * 100)

    if skipped_songs == 0:
        data["avg_seconds_played_before_skipping"] = 0
        data["percent_of_songs_skipped_before_3s"] = 0
        data["percent_of_songs_skipped_after_30s"] = 0
        data["percent_of_songs_skipped_after_120s"] = 0
    else:
        data["avg_seconds_played_before_skipping"] = round(skipped_df["minutes_played"].mean() * 60)
        data["percent_of_songs_skipped_before_3s"] = round(
            len(skipped_df[skipped_df["minutes_played"] < 3 / 60]) / skipped_songs * 100
        )
        data["percent_of_songs_skipped_after_30s"] = round(
            len(skipped_df[skipped_df["minutes_played"] > 30 / 60]) / skipped_songs * 100
        )
        data["percent_of_songs_skipped_after_120s"] = round(
            len(skipped_df[skipped_df["minutes_played"] > 2]) / skipped_songs * 100
        )

    shuffle_and_skipped = len(df[(df["reason_end"] == "forward button") & df["shuffle"]])
    not_shuffle_and_skipped = len(df[(df["reason_end"] == "forward button") & ~df["shuffle"]])

    if started_songs_shuffle == 0:
        data["percent_of_skipped_songs_using_shuffle"] = 0
        data["percent_of_skipped_songs_not_using_shuffle"] = 0
    else:
        data["percent_of_skipped_songs_using_shuffle"] = round(shuffle_and_skipped / started_songs_shuffle * 100)
        data["percent_of_skipped_songs_not_using_shuffle"] = round(
            not_shuffle_and_skipped / started_songs_shuffle * 100
        )

    data["percent_reason_start_forward_button"] = round(len(df[df["reason_start"] == "forward button"]) / len(df) * 100)
    data["percent_reason_start_back_button"] = round(len(df[df["reason_start"] == "back button"]) / len(df) * 100)
    data["percent_reason_start_trackdone"] = round(len(df[df["reason_start"] == "trackdone"]) / len(df) * 100)
    data["percent_reason_start_clickrow"] = round(len(df[df["reason_start"] == "clickrow"]) / len(df) * 100)

    data["pecent_of_played_songs_using_incognito_mode"] = round(
        df_full_play["incognito_mode"].sum() / played_songs * 100
    )

    data["average_play_count_per_song"] = round(df_full_play.groupby(["track"]).size().mean(), 1)

    data["percent_played_songs_reason_start_clickrow"] = round(
        len(df_full_play[df_full_play["reason_start"] == "clickrow"]) / played_songs * 100
    )

    for unit in ("artist", "track"):
        for top_n in (10, 100, 500):
            data[f"top_{top_n}_{unit}_play_count_percent"] = round(
                df_dict[f"cumulative_percent_play_count_{unit}"]["percent of played songs"].iloc[
                    min(top_n, data[f"unique_{unit}s_played"] - 1)
                ]
            )

    artists = df_dict["most_played_artists_total"]["artist"]
    tracks = df_dict["most_played_tracks_total"]["track"]
    for i in range(3):
        data[f"top_{i+1}_artist"] = artists.iloc[i] if len(artists) > i else "-"
        data[f"top_{i+1}_track"] = tracks.iloc[i] if len(tracks) > i else "-"

    return data


def get_df_random_sample(df, sample_count=1):
    df_sample = df.sample(sample_count)
    replace_track_artist(df_sample)
    replace_album_artist(df_sample)
    df_dict = df_sample.to_dict(orient="split")
    df_dict["data"].insert(0, df_dict["columns"])
    transposed_data = list(map(list, zip(*df_dict["data"])))
    df_dict = {"columns": ["columns", *[f"sample {i}" for i in range(1, sample_count + 1)]], "data": transposed_data}
    return df_dict


def get_df_dict(df, top_k=100, only_top_k=False):
    df_dict = {}

    df_dict.update(get_most_played_artists_tracks_albums_total(df, top_k))

    df_dict.update(
        get_most_played_artists_tracks_albums_total(
            df[df["reason_start"] == "clickrow"],
            top_k,
            "_reason_start_clickrow",
            column_name_muliplier_list=["track"],
        )
    )
    df_dict.update(get_top_songs_of_top_artists(df, top_k))
    if only_top_k:
        return df_dict

    df_dict.update(get_most_played_artist_track_album_monthly(df))
    df_dict.update(get_avg_track_length_monthly(df))
    df_dict.update(get_avg_play_count_per_song_yearly(df))
    df_dict.update(get_play_count_distribution(df))

    df_dict.update(get_yeary_track_artist_play_count(df))

    df_dict.update(get_hours_played_per_hour_of_the_day(df))
    df_dict.update(get_avg_hours_played_per_year_month_weekday(df))

    df_dict.update(get_plays_per_county_toal(df))
    df_dict.update(get_cumulative_percent_play_count_track_artists(df))
    return df_dict


def main():
    only_save_df_csv = False  # for caching the preprocessed df in a csv
    use_saved_df_csv = False

    if use_saved_df_csv:
        df = pd.read_csv("df.csv", parse_dates=["ts"])
    else:
        dir_path = sys.argv[1]
        df = pd.concat([read_json(os.path.join(dir_path, fn)) for fn in os.listdir(dir_path) if fn.endswith(".json")])
        df = preprocess_df(df)

    if only_save_df_csv:
        df["ts"] = df["ts"].dt.strftime("%Y-%m-%d %H:%M:%S")
        df.to_csv("df.csv", index=False)
        return

    df_dict = get_df_dict(df, top_k=20)
    post_process_dataframe_dict(df_dict)
    save_dataframe_dict(df_dict)

    single_values = get_single_values(df, df_dict)
    save_json("single_values", single_values)


country_code_to_name = {
    "AF": "Afghanistan",
    "AX": "Åland Islands",
    "AL": "Albania",
    "DZ": "Algeria",
    "AS": "American Samoa",
    "AD": "Andorra",
    "AO": "Angola",
    "AI": "Anguilla",
    "AQ": "Antarctica",
    "AG": "Antigua and Barbuda",
    "AR": "Argentina",
    "AM": "Armenia",
    "AW": "Aruba",
    "AU": "Australia",
    "AT": "Austria",
    "AZ": "Azerbaijan",
    "BS": "Bahamas",
    "BH": "Bahrain",
    "BD": "Bangladesh",
    "BB": "Barbados",
    "BY": "Belarus",
    "BE": "Belgium",
    "BZ": "Belize",
    "BJ": "Benin",
    "BM": "Bermuda",
    "BT": "Bhutan",
    "BO": "Bolivia, Plurinational State of",
    "BQ": "Bonaire, Sint Eustatius and Saba",
    "BA": "Bosnia and Herzegovina",
    "BW": "Botswana",
    "BV": "Bouvet Island",
    "BR": "Brazil",
    "IO": "British Indian Ocean Territory",
    "BN": "Brunei Darussalam",
    "BG": "Bulgaria",
    "BF": "Burkina Faso",
    "BI": "Burundi",
    "KH": "Cambodia",
    "CM": "Cameroon",
    "CA": "Canada",
    "CV": "Cape Verde",
    "KY": "Cayman Islands",
    "CF": "Central African Republic",
    "TD": "Chad",
    "CL": "Chile",
    "CN": "China",
    "CX": "Christmas Island",
    "CC": "Cocos (Keeling) Islands",
    "CO": "Colombia",
    "KM": "Comoros",
    "CG": "Congo",
    "CD": "Congo, the Democratic Republic of the",
    "CK": "Cook Islands",
    "CR": "Costa Rica",
    "CI": "Côte d'Ivoire",
    "HR": "Croatia",
    "CU": "Cuba",
    "CW": "Curaçao",
    "CY": "Cyprus",
    "CZ": "Czech Republic",
    "DK": "Denmark",
    "DJ": "Djibouti",
    "DM": "Dominica",
    "DO": "Dominican Republic",
    "EC": "Ecuador",
    "EG": "Egypt",
    "SV": "El Salvador",
    "GQ": "Equatorial Guinea",
    "ER": "Eritrea",
    "EE": "Estonia",
    "ET": "Ethiopia",
    "FK": "Falkland Islands (Malvinas)",
    "FO": "Faroe Islands",
    "FJ": "Fiji",
    "FI": "Finland",
    "FR": "France",
    "GF": "French Guiana",
    "PF": "French Polynesia",
    "TF": "French Southern Territories",
    "GA": "Gabon",
    "GM": "Gambia",
    "GE": "Georgia",
    "DE": "Germany",
    "GH": "Ghana",
    "GI": "Gibraltar",
    "GR": "Greece",
    "GL": "Greenland",
    "GD": "Grenada",
    "GP": "Guadeloupe",
    "GU": "Guam",
    "GT": "Guatemala",
    "GG": "Guernsey",
    "GN": "Guinea",
    "GW": "Guinea-Bissau",
    "GY": "Guyana",
    "HT": "Haiti",
    "HM": "Heard Island and McDonald Islands",
    "VA": "Holy See (Vatican City State)",
    "HN": "Honduras",
    "HK": "Hong Kong",
    "HU": "Hungary",
    "IS": "Iceland",
    "IN": "India",
    "ID": "Indonesia",
    "IR": "Iran, Islamic Republic of",
    "IQ": "Iraq",
    "IE": "Ireland",
    "IM": "Isle of Man",
    "IL": "Israel",
    "IT": "Italy",
    "JM": "Jamaica",
    "JP": "Japan",
    "JE": "Jersey",
    "JO": "Jordan",
    "KZ": "Kazakhstan",
    "KE": "Kenya",
    "KI": "Kiribati",
    "KP": "Korea, Democratic People's Republic of",
    "KR": "Korea, Republic of",
    "KW": "Kuwait",
    "KG": "Kyrgyzstan",
    "LA": "Lao People's Democratic Republic",
    "LV": "Latvia",
    "LB": "Lebanon",
    "LS": "Lesotho",
    "LR": "Liberia",
    "LY": "Libya",
    "LI": "Liechtenstein",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "MO": "Macao",
    "MK": "Macedonia, the Former Yugoslav Republic of",
    "MG": "Madagascar",
    "MW": "Malawi",
    "MY": "Malaysia",
    "MV": "Maldives",
    "ML": "Mali",
    "MT": "Malta",
    "MH": "Marshall Islands",
    "MQ": "Martinique",
    "MR": "Mauritania",
    "MU": "Mauritius",
    "YT": "Mayotte",
    "MX": "Mexico",
    "FM": "Micronesia, Federated States of",
    "MD": "Moldova, Republic of",
    "MC": "Monaco",
    "MN": "Mongolia",
    "ME": "Montenegro",
    "MS": "Montserrat",
    "MA": "Morocco",
    "MZ": "Mozambique",
    "MM": "Myanmar",
    "NA": "Namibia",
    "NR": "Nauru",
    "NP": "Nepal",
    "NL": "Netherlands",
    "NC": "New Caledonia",
    "NZ": "New Zealand",
    "NI": "Nicaragua",
    "NE": "Niger",
    "NG": "Nigeria",
    "NU": "Niue",
    "NF": "Norfolk Island",
    "MP": "Northern Mariana Islands",
    "NO": "Norway",
    "OM": "Oman",
    "PK": "Pakistan",
    "PW": "Palau",
    "PS": "Palestine, State of",
    "PA": "Panama",
    "PG": "Papua New Guinea",
    "PY": "Paraguay",
    "PE": "Peru",
    "PH": "Philippines",
    "PN": "Pitcairn",
    "PL": "Poland",
    "PT": "Portugal",
    "PR": "Puerto Rico",
    "QA": "Qatar",
    "RE": "Réunion",
    "RO": "Romania",
    "RU": "Russian Federation",
    "RW": "Rwanda",
    "BL": "Saint Barthélemy",
    "SH": "Saint Helena, Ascension and Tristan da Cunha",
    "KN": "Saint Kitts and Nevis",
    "LC": "Saint Lucia",
    "MF": "Saint Martin (French part)",
    "PM": "Saint Pierre and Miquelon",
    "VC": "Saint Vincent and the Grenadines",
    "WS": "Samoa",
    "SM": "San Marino",
    "ST": "Sao Tome and Principe",
    "SA": "Saudi Arabia",
    "SN": "Senegal",
    "RS": "Serbia",
    "SC": "Seychelles",
    "SL": "Sierra Leone",
    "SG": "Singapore",
    "SX": "Sint Maarten (Dutch part)",
    "SK": "Slovakia",
    "SI": "Slovenia",
    "SB": "Solomon Islands",
    "SO": "Somalia",
    "ZA": "South Africa",
    "GS": "South Georgia and the South Sandwich Islands",
    "SS": "South Sudan",
    "ES": "Spain",
    "LK": "Sri Lanka",
    "SD": "Sudan",
    "SR": "Suriname",
    "SJ": "Svalbard and Jan Mayen",
    "SZ": "Swaziland",
    "SE": "Sweden",
    "CH": "Switzerland",
    "SY": "Syrian Arab Republic",
    "TW": "Taiwan, Province of China",
    "TJ": "Tajikistan",
    "TZ": "Tanzania, United Republic of",
    "TH": "Thailand",
    "TL": "Timor-Leste",
    "TG": "Togo",
    "TK": "Tokelau",
    "TO": "Tonga",
    "TT": "Trinidad and Tobago",
    "TN": "Tunisia",
    "TR": "Turkey",
    "TM": "Turkmenistan",
    "TC": "Turks and Caicos Islands",
    "TV": "Tuvalu",
    "UG": "Uganda",
    "UA": "Ukraine",
    "AE": "United Arab Emirates",
    "GB": "United Kingdom",
    "US": "United States",
    "UM": "United States Minor Outlying Islands",
    "UY": "Uruguay",
    "UZ": "Uzbekistan",
    "VU": "Vanuatu",
    "VE": "Venezuela, Bolivarian Republic of",
    "VN": "Viet Nam",
    "VG": "Virgin Islands, British",
    "VI": "Virgin Islands, U.S.",
    "WF": "Wallis and Futuna",
    "EH": "Western Sahara",
    "YE": "Yemen",
    "ZM": "Zambia",
    "ZW": "Zimbabwe",
}

if __name__ == "__main__":
    if len(sys.argv[0]) > 0:
        sys.exit(main())
