# Spotify Data Documentation

This document describes the structure and contents of the datasets generated from Spotify listening history and API data.

## Listening History Dataset (`listening_history.parquet`)

Contains detailed listening history from Spotify, including both streaming and offline plays.

### Columns:
- `track_id` (string): Unique Spotify ID for the track
- `artist_id` (string): ID of the primary artist
- `ts` (datetime): Timestamp of when the track was played
- `ms_played` (int32): Duration played in milliseconds
- `reason_start` (string): How the track was started (e.g., "back button", "forward button", "play button")
- `reason_end` (string): How the track ended (e.g., "trackdone", "back button", "forward button", "end play")
- `full_play` (boolean): Whether the track was played to completion
- `conn_country` (string): Country code where the track was played
- `platform` (string): Device/platform used for playback
- `shuffle` (boolean): Whether shuffle mode was enabled
- `offline` (boolean): Whether the track was played offline
- `incognito_mode` (boolean): Whether incognito mode was enabled


## Tracks Dataset (`tracks.parquet`)

Contains detailed information about each unique track from the listening history.
The Spotify URL of the track `https://open.spotify.com/track/{track_id}`.

### Columns:
- `track_id` (string): Unique Spotify ID for the track
- `track_name` (string): Name of the track
- `track_duration_ms` (int64): Duration of the track in milliseconds
- `track_explicit` (boolean): Whether the track has explicit content
- `track_popularity` (int16): Popularity score (0-100)
- `track_number` (int16): Position of the track in its album
- `disc_number` (int16): Disc number for multi-disc albums
- `album_id` (string): ID of the album containing the track
- `artist_ids` (string): Semicolon-separated list of all artist IDs


## Artists Dataset (`artists.parquet`)

Contains information about artists associated with the tracks and albums.
The artist image is saved at `data/artist_images/{artist_id}.jpg`.
The URL of the wikidata `https://www.wikidata.org/wiki/{wikidata_entity_id}`.
The Spotify URL of the artist `https://open.spotify.com/artist/{artist_id}`.

### Columns:
- `artist_id` (string): Unique Spotify ID for the artist
- `artist_name` (string): Name of the primary artist
- `artist_followers` (int32): Number of followers on Spotify
- `artist_genres` (string): Semicolon-separated list of genres (combines Spotify and Wikidata genres)
- `artist_popularity` (int64): Popularity score (0-100)
- `top_track_ids` (string): Semicolon-separated list of the artist's top tracks
- `wikidata_entity_id` (string): Wikidata entity ID for the artist
- `gender` (string): Artist's gender from Wikidata
- `country` (string): Artist's country of citizenship for solo artists or country of origin for bands from Wikidata
- `birth_date` (datetime): Artist's date of birth from Wikidata
- `website` (string): Artist's official website from Wikidata


## Albums Dataset (`albums.parquet`)

Contains information about albums associated with the tracks.
The album image is saved at `data/album_images/{album_id}.jpg`.

### Columns:
- `album_id` (string): Unique Spotify ID for the album
- `album_name` (string): Name of the album
- `album_type` (string): Type of album (e.g., album, single, compilation)
- `album_total_tracks` (int16): Total number of tracks in the album
- `album_release_year` (int16): Year the album was released (0 values should be treated as unknown)
- `album_label` (string): Record label that released the album
- `album_popularity` (int16): Popularity score (0-100)
- `album_artist_ids` (string): Semicolon-separated list of artist IDs
- `album_track_ids` (string): Semicolon-separated list of track IDs


## Main Dataset (`listening_history_with_internet_data.parquet`)

This dataset contains the listening history with the spotify and wikidata data merged.
This means that it contains all the information from the other datasets and it can be used to more easily query the data.

The dataset is created like this:

```python
df_all = (
    df_history
        .merge(df_tracks, on='track_id', how='left')
        .merge(df_albums, on='album_id', how='left')
        .merge(df_artists, on='artist_id', how='left')
    )
df_all["hours_played"] = df_all["ms_played"] / (1000 * 60 * 60)
df_all.to_parquet(output_parquet, index=False)
```

## Creating a playlist from a list of track ids

```python
from util import create_spotify_playlist
track_ids = results["track_id"].tolist()
create_spotify_playlist(track_ids, "playlist name")
```

## Usage Examples

### Top 10 artists by hours played

<details>
<summary>Show code</summary>

```python
results = (
    df
    .groupby('artist_name')
    .agg(
        hours_played=('hours_played', lambda x: x.sum().round(2)),
        full_play_count=('full_play', 'sum'),
        skip_count=('full_play', lambda x: (~x).sum()),
    )
    .reset_index()
    .sort_values('hours_played', ascending=False)
    .head(10)
)
results
```
</details>

### Top 10 tracks from an artist by hours played

<details>
<summary>Show code</summary>

```python
artist_name = "Frank Ocean"
results = (
    df[df['artist_name'] == artist_name]
    .groupby('track_id')
    .agg(
        track_name=('track_name', 'first'),
        album_name=('album_name', 'first'),
        hours_played=('hours_played', lambda x: x.sum().round(2)),
        full_play_count=('full_play', 'sum'),
        skip_count=('full_play', lambda x: (~x).sum()),
    )
    .reset_index()
    .drop(columns=['track_id'])
    .sort_values('hours_played', ascending=False)
    .head(10)
)
results
```
</details>

### First songs played

<details>
<summary>Show code</summary>

```python
results = (
    df
    .sort_values('ts', ascending=True)
    .head(5)[["ts", "track_name", "artist_name", "reason_start", "ms_played", "track_duration_ms", "reason_end", "platform", "conn_country", "website", "track_id"]]
    .drop(columns=["track_id"])
)
results
```
</details>  

### Artists gender by hours played

<details>
<summary>Show code</summary>

```python
results = (
    df
    .groupby('gender', dropna=False)
    .agg({
        'hours_played': lambda x: x.sum().round(2),
        'full_play': 'sum',
    })
    .reset_index()
    .sort_values('full_play', ascending=False)
)
results
```
</details>

### Top 20 tracks from female artists by hours played (one per artist) in the last 3 years

<details>
<summary>Show code</summary>

```python
three_years_ago = datetime.now() - timedelta(days=3*365)
results = (
    df[(df['gender'] == "female") & (df['ts'] >= three_years_ago)]
    .groupby('track_id')
    .agg({
        'track_name': 'first',
        'artist_name': 'first',
        'album_name': 'first',
        'album_release_year': 'first',
        'country': 'first',
        'gender': 'first',
        'hours_played': lambda x: x.sum().round(2),
        'full_play': 'sum',
    })
    .reset_index()
    .sort_values('hours_played', ascending=False)
    # Group by artist_name and take the top track for each
    .groupby('artist_name')
    .first()
    .reset_index()
    .reindex(columns=['artist_name', 'track_name', 'album_name', 'album_release_year', 'country', 'gender', 'hours_played', 'full_play', 'track_id'])
    .sort_values('hours_played', ascending=False)
    .head(20)
)
results
```

It is also possible to create a playlist with all the tracks using the `create_spotify_playlist` function in `util.py` and the `track_ids` column.

```python
from util import create_spotify_playlist
track_ids = results["track_id"].tolist()
create_spotify_playlist(track_ids, "my top tracks from female artists in the last 3 years")
```
</details>

### Artists without wikidata info, sorted by hours played

<details>
<summary>Show code</summary>

```python
results = (
    df[~df["wikidata_entity_id"].notna()]
    .groupby("artist_id")
    .agg({
        "artist_name": "first",
        "hours_played": "sum",
        "artist_popularity": "first",
        "wikidata_entity_id": "first",
    })
    .reset_index()
    .sort_values("hours_played", ascending=False)
)
results[0:10]
```
</details>

### Artists without wikidata info, sorted by popularity

<details>
<summary>Show code</summary>

```python
results = (
    df[~df["wikidata_entity_id"].notna()]
    .groupby("artist_id")
    .agg({
        "artist_name": "first",
        "artist_popularity": "first",
        "wikidata_entity_id": "first",
    })
    .reset_index()
    .sort_values("artist_popularity", ascending=False)
)
results[0:10]
```
</details>

### Top 10 artists by country

<details>
<summary>Show code</summary>

```python
results = (
    df
    .groupby('country')
    .agg({
        'hours_played': lambda x: x.sum().round(2),
        'full_play': 'sum',
    })
    .reset_index()
    .sort_values('full_play', ascending=False)
    .head(10)
)
results
```
</details>


### Top 10 tracks from solo artists from 1950-1970

<details>
<summary>Show code</summary>

```python
results = (
    df[(df['is_band'] == False) & (df['album_release_year'] >= 1950) & (df['album_release_year'] <= 1970)]
    .groupby('track_id')
    .agg({
        'track_name': 'first',
        'artist_name': 'first',
        'album_name': 'first',
        'album_release_year': 'first',
        'country': 'first',
        'hours_played': lambda x: x.sum().round(2),
        'full_play': 'sum',
    })
    .reset_index()
    .drop(columns=['track_id'])
    .sort_values('hours_played', ascending=False)
    .head(10)
)
results
```
</details>


### Top 20 genres by hours played

<details>
<summary>Show code</summary>

```python
results = (
    df[df['artist_genres'].notna()]
    .assign(genres=lambda x: x['artist_genres'].str.split(';'))
    .explode('genres')
    .groupby('genres')
    .agg(
        hours_played=('hours_played', lambda x: int(x.sum().round(0))),
    )
    .sort_values('hours_played', ascending=False)
    .reset_index()
    .head(20)
)
results
```
</details>


### Top 10 tracks from artists with 'classical' in their genre

<details>
<summary>Show code</summary>

```python
results = (
    df[df['artist_genres'].str.contains('classical', case=False, na=False)]
    .groupby('track_id')
    .agg({
        'track_name': 'first',
        'artist_name': 'first',
        'hours_played': lambda x: x.sum().round(2),
        'full_play': 'sum',
    })
    .reset_index()
    .drop(columns=['track_id'])
    .sort_values('full_play', ascending=False)
    .head(10)
)
results
```
</details>

### Percentage of Rock, Hip-Hop, and Pop songs played over time

<details>
<summary>Show code</summary>

```python
genre_by_year = (
    df[df["full_play"]]
    .assign(
        year=lambda x: x['ts'].dt.year,
        is_rock=lambda x: x['artist_genres'].str.contains('rock', case=False),
        is_hiphop=lambda x: x['artist_genres'].str.contains('hip.?hop', case=False, regex=True),
        is_pop=lambda x: x['artist_genres'].str.contains('pop', case=False)
    )
    .groupby('year')
    .agg(
        rock_full_play=('is_rock', 'sum'),
        hiphop_full_play=('is_hiphop', 'sum'),
        pop_full_play=('is_pop', 'sum'),
        total_full_play=('full_play', 'sum')
    )
    .assign(
        rock_percent=lambda x: (x['rock_full_play'] / x['total_full_play'] * 100).round(2),
        hiphop_percent=lambda x: (x['hiphop_full_play'] / x['total_full_play'] * 100).round(2),
        pop_percent=lambda x: (x['pop_full_play'] / x['total_full_play'] * 100).round(2)
    )
)

# Create the plot
plt.figure(figsize=(12, 6))
genre_by_year[['rock_percent', 'hiphop_percent', 'pop_percent']].plot(kind='line', marker='o')
plt.title('Percentage of Rock, Hip-Hop, and Pop Songs Played Over Time')
plt.xlabel('Year')
plt.ylabel('Percentage of Songs Played')
plt.legend(['Rock', 'Hip-Hop', 'Pop'], title='Genre')
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()
```
</details>


### Top 5 bands and top 5 solo artists by hours played

<details>
<summary>Show code</summary>

```python
results = pd.concat([
    # Top 5 solo artists
    df[df['is_band'] == False]
    .groupby('artist_name')
    .agg(
        hours_played=('hours_played', lambda x: x.sum().round(2)),
        full_play_count=('full_play', 'sum'),
        is_band=('is_band', 'first')
    )
    .reset_index()
    .sort_values('hours_played', ascending=False)
    .head(5),

    # Top 5 bands
    df[df['is_band'] == True]
    .groupby('artist_name')
    .agg(
        hours_played=('hours_played', lambda x: x.sum().round(2)),
        full_play_count=('full_play', 'sum'),
        is_band=('is_band', 'first')
    )
    .reset_index()
    .sort_values('hours_played', ascending=False)
    .head(5)
])
results
```
</details>

### Top artist for each of the 10 biggest countries by hours played

<details>
<summary>Show code</summary>

```python
results = (
    df
    # First get the top 10 countries by total hours
    .groupby('country')
    .agg(total_hours=('hours_played', lambda x: int(x.sum().round(0))))
    .nlargest(10, 'total_hours')
    .reset_index()
    .merge(
        # Get the top artist for each country
        df.groupby(['country', 'artist_name'])
        .agg(
            hours_played_artist=('hours_played', lambda x: int(x.sum().round(0))),
            full_play_count_artist=('full_play', 'sum')
        )
        .reset_index()
        .sort_values('hours_played_artist', ascending=False)
        .groupby('country')
        .first()
        .reset_index(),
        on='country'
    )
    .sort_values('total_hours', ascending=False)
)
results
```
</details>


### Top 20 songs that were first discovered in a specific year

<details>
<summary>Show code</summary>

```python
year = 2020
results = (
    # First get the first play date for each track across all time
    df.groupby('track_id')['ts']
    .min()
    .reset_index()
    .rename(columns={'ts': 'first_play'})
    # Then merge back with original data and filter for {year} discoveries
    .merge(df, on='track_id')
    .query(f'first_play.dt.year == {year}')
    .groupby('track_id')
    .agg({
        'track_name': 'first',
        'artist_name': 'first',
        'album_name': 'first',
        'album_release_year': 'first',
        'full_play': 'sum',
        'hours_played': lambda x: x.sum().round(2),
        'first_play': 'first'
    })
    .reset_index()
    .sort_values('full_play', ascending=False)
    .head(20)
    .drop(columns=['track_id'])
)
results
```
</details>


### Top 10 songs that were partially played a lot, but never fully played

<details>
<summary>Show code</summary>

```python
results = (
    df
    .groupby('track_id')
    .agg({
        'track_name': 'first',
        'artist_name': 'first',
        'album_name': 'first',
        'full_play': 'max',  # If max is False, means never fully played
        'hours_played': lambda x: x.sum().round(2),
        'ms_played': 'count'  # Number of attempts
    })
    .reset_index()
    .query('full_play == False')  # Only get tracks never finished
    .drop(columns=['track_id', 'full_play'])
    .rename(columns={'ms_played': 'partial_play_count'})
    .sort_values(['partial_play_count', 'hours_played'], ascending=[False, False])  # Sort by most attempts
    .head(10)
)
results
```
</details>


### The least played song for my top 10 albums

<details>
<summary>Show code</summary>

```python
results = (
    # First just get top 10 albums by total hours
    df.groupby(['artist_name', 'album_name'])
    .agg(
        total_album_hours=('hours_played', lambda x: x.sum().round(1)),
    )
    .nlargest(10, 'total_album_hours')
    .reset_index()
    # Now merge with track-level stats for just these albums
    .merge(
        df.groupby(['artist_name', 'album_name', 'track_name'])
        .agg({
            'hours_played': lambda x: x.sum().round(1),
            'full_play': 'sum'
        })
        .reset_index(),
        on=['artist_name', 'album_name']
    )
    # Calculate average full plays per album
    .assign(
        avg_full_play=lambda x: x.groupby(['artist_name', 'album_name'])['full_play'].transform('mean').round(1)
    )
    # Get the least played song for each album
    .sort_values('full_play')
    .groupby(['artist_name', 'album_name'])
    .first()
    .sort_values('total_album_hours', ascending=False)
    .reset_index()
)
results
```
</details>


### Get my personal one hit wonder artists (one popular song but rarely listen to others)

<details>
<summary>Show code</summary>

```python
results = (
    # First get play counts for each track by artist
    df.groupby(['artist_name', 'track_name'])
    .agg({
        'full_play': 'sum',
        'hours_played': lambda x: x.sum().round(2)
    })
    .reset_index()
    # Get stats about each artist's tracks
    .groupby('artist_name')
    .agg(
        track_name=('track_name', 'first'),
        full_play_max=('full_play', 'max'),
        full_play_sum=('full_play', 'sum'),
        hours_played=('hours_played', 'sum')
    )
    .reset_index()
    # Calculate plays for other tracks and filter
    .assign(
        top_track=lambda x: x['track_name'],
        top_track_plays=lambda x: x['full_play_max'],
        total_plays=lambda x: x['full_play_sum'],
        other_tracks_plays=lambda x: x['full_play_sum'] - x['full_play_max']
    )
)

# Filter and sort the results
results = (
    results[
        (results['top_track_plays'] > 20) & 
        (results['other_tracks_plays'] < 10)
    ]
    [['artist_name', 'top_track', 'top_track_plays', 'hours_played', 'other_tracks_plays']]
    .sort_values('top_track_plays', ascending=False)
    .head(10)
)
results
```
</details>


### Get songs not played in the last 3 years

<details>
<summary>Show code</summary>

```python
three_years_ago = datetime.now() - timedelta(days=3*365)
results = (
    df
    .groupby('track_id')
    .agg({
        'track_name': 'first',
        'artist_name': 'first',
        'album_name': 'first',
        'ts': 'max',  # Get the most recent play
        'full_play': 'sum',
        'hours_played': lambda x: x.sum().round(2)
    })
    .reset_index()
    # Filter for songs not played in last 3 years
    .loc[lambda x: x['ts'] < three_years_ago]
    .drop(columns=['track_id'])
    .rename(columns={'ts': 'last_play'})
    .sort_values('full_play', ascending=False)
    .head(10)
)
results
```
</details>
