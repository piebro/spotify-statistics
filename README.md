# Personal Spotify Statistics

I like statistics and listening to music, and I also enjoy the yearly [Spotify Wrapped](https://www.spotify.com/wrapped/). After watching one at the end of each year, I am always interested in more in-depth statistics over multiple years. That's why I created a [website](https://piebro.github.io/spotify-statistics) to generate personal Spotify usage statistics.

This works well because, a few years ago, the EU passed the [GDPR Act](https://www.wired.co.uk/article/what-is-gdpr-uk-eu-legislation-compliance-summary-fines-2018), which enables EU citizens to access all personal data a company has stored about you. Spotify stores a log of your listening history, including partial listens. This data log is a treasure if you are interested in your own listening behavior. You can request your `Extended streaming history` data at https://www.spotify.com/us/account/privacy/.

The data is processed with the `data_crunching.py` script to generate statistics for questions that I have about my listening behavior. The [website](https://piebro.github.io/spotify-statistics) makes it easy to use the script to generate your own personal statistics. The data is only processed in your browser and never leaves your computer.

## Some thoughts about the data

I downloaded my own data several times over the past few months without any issues. However, the last time I downloaded it, there was some missing data for the year 2017. For this time period, the reason_end data field consistently showed none instead of the actual reason why the song ended. If you notice anything unusual in your statistics, it might be because the Spotify data export was inaccurate, and I would recommend re-downloading your data.

The data is divided into multiple JSON files, each approximately 10.5MB in size, containing the streaming history. This JSON is comprised of a lengthy list of objects, each representing a listening log. Additionally, there's a PDF file that offers explanations for each data field in various languages. As of October 2023, the table is structured as follows:

| Technical Field                      | Contains                                                                                                                                                      |
|--------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ts                                   | This field is a timestamp indicating when the track stopped playing in UTC (Coordinated Universal Time). The order is year, month and day followed by a timestamp in military time.  |
| username                             | This field is your Spotify username.                                                                                                                          |
| platform                             | This field is the platform used when streaming the track (e.g. Android OS, Google Chromecast).                                                                |
| ms_played                            | This field is the number of milliseconds the stream was played.                                                                                               |
| conn_country                         | This field is the country code of the country where the stream was played (e.g. SE - Sweden).                                                                 |
| Ip_addr_decrypted                    | This field contains the IP address logged when streaming the track.                                                                                           |
| user_agent_decrypted                 | This field contains the user agent used when streaming the track (e.g. a browser, like Mozilla Firefox, or Safari)                                            |
| master_metadata_track_name           | This field is the name of the track.                                                                                                                          |
| master_metadata_album_artist_name    | This field is the name of the artist, band or podcast.                                                                                                        |
| master_metadata_album_album_name     | This field is the name of the album of the track.                                                                                                             |
| spotify_track_uri                    | A Spotify URI, uniquely identifying the track in the form of “spotify:track:<base-62 string>”. A Spotify URI is a resource identifier that you can enter, for example, in the Spotify Desktop client’s search box to locate an artist, album, or track. |
| episode_name                         | This field contains the name of the episode of the podcast.                                                                                                   |
| episode_show_name                    | This field contains the name of the show of the podcast.                                                                                                      |
| spotify_episode_uri                  | A Spotify Episode URI, uniquely identifying the podcast episode in the form of “spotify:episode:<base-62 string>”. A Spotify Episode URI is a resource identifier that you can enter, for example, in the Spotify Desktop client’s search box to locate an episode of a podcast. |
| reason_start                         | This field is a value telling why the track started (e.g. “trackdone”)                                                                                        |
| reason_end                           | This field is a value telling why the track ended (e.g. “endplay”).                                                                                           |
| shuffle                              | This field has the value True or False depending on if shuffle mode was used when playing the track.                                                          |
| skipped                              | This field indicates if the user skipped to the next song.                                                                                                    |
| offline                              | This field indicates whether the track was played in offline mode (“True”) or not (“False”).                                                                  |
| offline_timestamp                    | This field is a timestamp of when offline mode was used, if used.                                                                                             |
| incognito_mode                       | This field indicates whether the track was played in incognito mode (“True”) or not (“False”).                                                                |

I perform some preprocessing to work with the data more easily.

I initially used the `ts` (timestamp) as my standard time reference, but I noticed that there were instances where multiple songs were logged at the exact same time. I suspect this might have occurred due to a lack of internet connection at those moments. That's why I looked at the `offline_timestamp`. The time in this field is saved as a [Unix timestamp](https://www.unixtimestamp.com/). However, some entries in this field don't make sense (they were less than 100 and would be from the 1970s). To address this, I utilize the `offline_timestamp` if it seems plausible; otherwise, I revert to using the normal `ts` for the timestamp.

I'm unsure how Spotify determined if a song was `skipped`. I delved into the `ms_played` and `reason_end` data for `skipped` songs but couldn't make sense of it. For these statistics, a song is considered skipped if the reason for the song ending is the pressing of the forward button. A song is marked as fully played when the reason for the end of the song is `trackdone`.

## Using the Spotify API

1. Go to https://developer.spotify.com/dashboard/applications
2. Click `Create an app`
3. Enter a name and description
4. Click `Create`
5. Click `Edit settings`
6. Click `Add new redirect URI` and enter `http://localhost:8888/callback`
7. Click `Save`
8. Copy the client ID and client secret
9. Create a .env file with the following variables:
    ```bash
    SPOTIFY_CLIENT_ID=<spotify-client-id>
    SPOTIFY_CLIENT_SECRET=<spotify-client-secret>
    ```
10. run `uv run src/add_refeshtoken_to_env.py` to add the spotify refresh token to the .env file


```bash
uv run src/create_db.py "Path-To-Spotify-Extended-Streaming-History-Folder"
uv run src/enrich_with_internet_data.py
```

## Contributing

Contributions to this project are welcome. Feel free to report bugs, suggest ideas or create merge requests.

## Developing

[uv](https://docs.astral.sh/uv/getting-started/installation/) is used in the project to run Python.

```bash
# Use the script to update the data in the folder website/assets
uv run website/data_crunching.py "Path-To-Spotify-Extended-Streaming-History-Folder"

# Run a simple Python server to view your stats in the browser
uv run -m http.server

# Open http://0.0.0.0:8000/ in your browser
```

### Formatting and linting

The project uses the Python code formatter and linter [Ruff](https://github.com/astral-sh/ruff) for python.

```bash
uv run ruff check src/*.py --fix
uv run ruff format src/*.py
```

[Prettier](https://prettier.io/playground/) is used for linting the `website/index.js` file with a `print-width` of 120, `tab-width` of 4, and using single quotes. Additionally, I used [Stylelint](https://stylelint.io/demo/) for linting the `website/index.css` file.


## Website Statistics

There is lightweight tracking for the website using Plausible. Anyone interested can view these statistics at https://plausible.io/piebro.github.io%2Fspotify-statistics. Note that only users without an AdBlocker are counted, so these statistics underestimate the actual number of visitors. I would assume that a significant number of people visiting the site, including myself, have an AdBlocker enabled.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.