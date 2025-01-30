# Spotify Data Documentation

This document describes the structure and contents of the datasets generated from Spotify listening history and API data.

## Listening History Dataset (`listening_history.csv`)

Contains detailed listening history from Spotify, including both streaming and offline plays.

### Columns:
- `track`: Combined track name and artist (format: "track_name~~sep~~artist_name")
- `artist`: Artist name
- `album`: Combined album name and artist (format: "album_name~~sep~~artist_name")
- `year_month_day`: Date of play (YYYY-MM-DD)
- `day_name`: Day of the week
- `minutes_played`: Duration played in minutes
- `reason_start`: How the track was started (e.g., "back button", "forward button", "play button")
- `reason_end`: How the track ended (e.g., "trackdone", "back button", "forward button", "end play")
- `conn_country`: Country code where the track was played
- `platform`: Device/platform used for playback
- `shuffle`: Whether shuffle mode was active (boolean)
- `full_play`: Whether the track was played to completion (boolean)
- `offline`: Whether the track was played offline (boolean)
- `incognito_mode`: Whether incognito mode was active (boolean)
- `ts`: Timestamp of play (YYYY-MM-DD HH:MM:SS)
- `year`: Year of play
- `year_month`: Year and month of play (YYYY-MM)
- `month`: Month of play (1-12)
- `month_index`: Months since first play (0-based index)
- `ms_played`: Duration played in milliseconds
- `hours_played`: Duration played in hours
- `track_id`: Spotify track ID

## Tracks Dataset (`tracks.csv`)

Contains detailed information about each unique track from the listening history.

### Columns:
- `track_id`: Spotify track ID
- `track_name`: Name of the track
- `track_duration_ms`: Track duration in milliseconds
- `track_explicit`: Whether the track has explicit content (boolean)
- `track_popularity`: Track popularity score (0-100)
- `track_number`: Position of the track in its album
- `disc_number`: Disc number for multi-disc albums
- `spotify_url`: Spotify URL for the track
- `album_id`: ID of the album containing the track
- `artist_ids`: Semicolon-separated list of artist IDs

## Albums Dataset (`albums.csv`)

Contains information about albums associated with the tracks.

### Columns:
- `album_id`: Spotify album ID
- `album_name`: Name of the album
- `album_type`: Type of album (e.g., album, single, compilation)
- `total_tracks`: Total number of tracks in the album
- `release_date`: Release date of the album
- `release_date_precision`: Precision of the release date (day, month, or year)
- `label`: Record label
- `popularity`: Album popularity score (0-100)
- `spotify_url`: Spotify URL for the album
- `artist_ids`: Semicolon-separated list of artist IDs
- `track_ids`: Semicolon-separated list of track IDs
- `image_url`: URL of the album cover image
- `copyright_text`: Copyright text
- `copyright_type`: Type of copyright

## Artists Dataset (`artists.csv`)

Contains information about artists associated with the tracks and albums.

### Columns:
- `artist_id`: Spotify artist ID
- `artist_name`: Name of the artist
- `followers`: Number of Spotify followers
- `genres`: Semicolon-separated list of genres
- `popularity`: Artist popularity score (0-100)
- `spotify_url`: Spotify URL for the artist
- `image_url`: URL of the artist's profile image
