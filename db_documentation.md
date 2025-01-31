# Spotify Data Documentation

This document describes the structure and contents of the datasets generated from Spotify listening history and API data.

## Listening History Dataset (`listening_history.parquet`)

Contains detailed listening history from Spotify, including both streaming and offline plays.

### Columns:
- `track_id` (string): Unique Spotify ID for the track
- `artist_id` (string): ID of the primary artist
- `album_id` (string): ID of the album containing the track
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
- `citizenship` (string): Artist's country of citizenship from Wikidata
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
