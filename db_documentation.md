# Spotify Data Documentation

This document describes the structure and contents of the datasets generated from Spotify listening history and API data.

## Listening History Dataset (`listening_history.parquet`)

Contains detailed listening history from Spotify, including both streaming and offline plays.

### Columns:
- `track_id` (string): Unique Spotify ID for the track
- `track` (string): Name of the track
- `artist` (string): Name of the primary artist
- `album` (string): Name of the album
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
- `main_artist_id` (string): ID of the primary artist
- `album_id` (string): ID of the album containing the track

## Tracks Dataset (`tracks.parquet`)

Contains detailed information about each unique track from the listening history.

### Columns:
- `track_id` (string): Unique Spotify ID for the track
- `track_name` (string): Name of the track
- `track_duration_ms` (int64): Duration of the track in milliseconds
- `track_explicit` (boolean): Whether the track has explicit content
- `track_popularity` (int16): Popularity score (0-100)
- `track_number` (int16): Position of the track in its album
- `disc_number` (int16): Disc number for multi-disc albums
- `album_id` (string): ID of the album containing the track
- `main_artist_id` (string): ID of the primary artist
- `artist_ids` (string): Semicolon-separated list of all artist IDs

## Albums Dataset (`albums.parquet`)

Contains information about albums associated with the tracks.

### Columns:
- `album_id` (string): Unique Spotify ID for the album
- `album_name` (string): Name of the album
- `album_type` (string): Type of album (e.g., album, single, compilation)
- `album_total_tracks` (int16): Total number of tracks in the album
- `album_release_year` (int16): Year the album was released
- `album_label` (string): Record label that released the album
- `album_popularity` (int16): Popularity score (0-100)
- `album_artist_ids` (string): Semicolon-separated list of artist IDs
- `album_track_ids` (string): Semicolon-separated list of track IDs
- `album_image_url` (string): URL of the album cover image
- `album_copyright_text` (string): Copyright text
- `album_copyright_type` (string): Type of copyright

## Artists Dataset (`artists.parquet`)

Contains information about artists associated with the tracks and albums.

### Columns:
- `artist_id` (string): Unique Spotify ID for the artist
- `artist_name` (string): Name of the artist
- `artist_followers` (int32): Number of followers on Spotify
- `artist_genres` (string): Semicolon-separated list of genres
- `artist_popularity` (int16): Popularity score (0-100)
- `artist_image_url` (string): URL of the artist's profile image
