let pyodide = null;
let displayUserData = false;
let data_cache = {};
data_cache['basics_dict'] = {
    first_day: '2015-06-24',
    last_day: '2023-08-24',
    number_of_days: 2983,
    number_of_days_with_tracks_played: 2461,
    percent_of_days_with_tracks_played: 83,
    played_songs: 67982,
    played_songs_per_day: 23,
    unique_tracks_played: 14513,
    unique_artists_played: 3706,
    unique_albums_played: 7052,
    unique_tracks_played_per_artist: 3.9,
    listening_hours: 4951,
    listening_hours_per_day: '1:40',
    percent_of_played_songs_using_shuffle: 58,
    skipped_songs: 86954,
    percent_of_skipped_songs: 48,
    avg_seconds_played_before_skipping: 20,
    percent_of_songs_skipped_before_3s: 64,
    percent_of_songs_skipped_after_30s: 17,
    percent_of_songs_skipped_after_120s: 5,
    percent_of_skipped_songs_using_shuffle: 55,
    percent_of_skipped_songs_not_using_shuffle: 18,
    percent_reason_start_forward_button: 48,
    percent_reason_start_back_button: 4,
    percent_reason_start_trackdone: 37,
    percent_reason_start_clickrow: 10,
    percent_of_played_songs_using_incognito_mode: 0,
    average_play_count_per_song: 4.7,
    percent_played_songs_reason_start_clickrow: 10,
    top_10_artist_play_count_percent: 20,
    top_100_artist_play_count_percent: 61,
    top_500_artist_play_count_percent: 87,
    top_10_track_play_count_percent: 1,
    top_100_track_play_count_percent: 7,
    top_500_track_play_count_percent: 24,
    top_1_artist: 'Gorillaz',
    top_1_track: 'F\u00fcchse',
    top_2_artist: 'Lana Del Rey',
    top_2_track: 'Me, Myself & I',
    top_3_artist: 'Kanye West',
    top_3_track: 'Nikes',
};

basic_text = `
<ul>
<li>My top three artists are: <span class="highlight">{top_1_artist}</span>, <span class="highlight">{top_2_artist}</span> and <span class="highlight">{top_3_artist}</span>.</li>
<li>My top three songs are: <span class="highlight">{top_1_track}</span>, <span class="highlight">{top_2_track}</span> and <span class="highlight">{top_3_track}</span>.</li>
<li>I listened to <span class="highlight">{played_songs}</span> songs in <span class="highlight">{listening_hours}</span> hours.</li>
<li>I played <span class="highlight">{unique_artists_played}</span> unique artists and <span class="highlight">{unique_albums_played}</span> unique albums.</li>
<li>On average, I played a song <span class="highlight">{average_play_count_per_song}</span> times.</li>
<li>I skipped <span class="highlight">{percent_of_skipped_songs}%</span> of all started songs and <span class="highlight">{percent_of_played_songs_using_shuffle}%</span> of all songs I listened to were played using shuffle.</li>
</ul>
`;

advanced_basic_text = `
<ul>
<li>My records begin on {first_day} and end on {last_day}. That's a span of {number_of_days} days.</li>
<li>I played songs on {number_of_days_with_tracks_played} days, which account for {percent_of_days_with_tracks_played}% of all days.</li>
<li>I played {played_songs} songs, totaling {listening_hours} hours. That's an average of about {played_songs_per_day} tracks or {listening_hours_per_day} hours per day.</li>
<li>I have listened to {unique_tracks_played} unique songs, from {unique_artists_played} artists and {unique_albums_played} albums. That's an average of about {unique_tracks_played_per_artist} songs per artist.</li>
<li>I play a song, on average, {average_play_count_per_song} times.</li>
<li>About {percent_of_played_songs_using_shuffle}% of all songs I listened to were played using shuffle.</li>
<li>I skipped {skipped_songs} songs, which is about {percent_of_skipped_songs}% of all songs I started.</li>
<li>On average, I listen to a song for {avg_seconds_played_before_skipping} seconds before skipping it. Of the songs I skip, {percent_of_songs_skipped_before_3s}% are skipped within 3 seconds, while {percent_of_songs_skipped_after_30s}% are skipped after more than 30 seconds and {percent_of_songs_skipped_after_120s}% after more than 2 minutes.</li>
<li>I skip {percent_of_skipped_songs_using_shuffle}% of all started songs when using shuffle and {percent_of_skipped_songs_not_using_shuffle}% when not using shuffle.</li>
<li>I started {percent_reason_start_forward_button}% of my songs because I clicked the forward button, {percent_reason_start_back_button}% because I clicked the back button, {percent_reason_start_trackdone}% because the previous song ended and {percent_reason_start_clickrow}% because I clicked on the song.</li>
<li>I played {percent_of_played_songs_using_incognito_mode}% of my songs using incognito mode.</li>
</ul>
`;

top_artists_and_songs_text = `
<ul>
<li>My top 10 artists contribute to {top_10_artist_play_count_percent}% of my played songs.</li>
<li>My top 100 artists contribute to {top_100_artist_play_count_percent}% of my played songs.</li>
<li>My top 500 artists contribute to {top_500_artist_play_count_percent}% of my played songs.</li>
<li>My top 10 songs contribute to {top_10_track_play_count_percent}% of my played songs.</li>
<li>My top 100 songs contribute to {top_100_track_play_count_percent}% of my played songs.</li>
<li>My top 500 songs contribute to {top_500_track_play_count_percent}% of my played songs.</li>
</ul>
`;

content_functions = {
    basics: [addText(basic_text, 'basics_dict')],
    general: [addText(advanced_basic_text, 'basics_dict')],
    'most played artists': [addTableRowWise('most played artists', 'most_played_artists_total', { show_rank: true })],
    'most played songs': [addTableRowWise('most played songs', 'most_played_tracks_total', { show_rank: true })],
    'most played albums': [addTableRowWise('most played albums', 'most_played_albums_total', { show_rank: true })],
    'most played per month': [
        addTableRowWise('most played artist, song and album per month', 'most_played_artists_track_album_monthly'),
    ],
    'song stats': [
        addSingleLinePlot('average play count per song each year', 'avg_play_count_per_song_yearly', {
            y_axis_year: true,
        }),
        addSingleLinePlot('distribution of how many songs are played how often', 'play_count_distribution'),
    ],
    'unique and new played songs': [
        addMultiLinePlot('yearly song play count', 'yearly_track_play_count', 'songs played'),
    ],
    'cumulative play count': [
        addText(top_artists_and_songs_text, 'basics_dict'),
        addSingleLinePlot(
            'cumulative play count by artist count in percent of all played songs',
            'cumulative_percent_play_count_artist',
            { type: 'scatter' },
        ),
        addSingleLinePlot(
            'cumulative play count by song count in percent of all played songs',
            'cumulative_percent_play_count_track',
            { type: 'scatter' },
        ),
    ],
    'play time per day': [
        addSingleLinePlot('average hours played per day per year and month', 'avg_hours_played_per_year_month', {
            y_hour: true,
        }),
        addSingleLinePlot('average hours played per day per year', 'avg_hours_played_per_year', { y_hour: true }),
        addSingleLinePlot('average hours played per day per month', 'avg_hours_played_per_month', { y_hour: true }),
        addSingleLinePlot('average hours played per day per weekday', 'avg_hours_played_per_day_name', {
            y_hour: true,
        }),
        addSingleLinePlot('percent of play time per hour of the day', 'hours_played_percent_per_hour_of_the_day', {
            y_hour: false,
        }),
    ],
    'songs of top artists': [
        addTableRowWise('top songs of the top artists', 'top_songs_of_top_artists', { sorting: false }),
    ],
    'most played songs clicked on': [
        addTableRowWise(
            'most played songs that started because they were clicked on',
            'most_played_tracks_total_reason_start_clickrow',
            { show_rank: true },
        ),
    ],
    countries: [addTableRowWise('plays per county in total', 'plays_per_county_total')],
    'average song length': [
        addSingleLinePlot('average song length per month', 'avg_track_length_monthly', { y_minute: true }),
    ],
    sample_data: [addTableRowWise('title sample_data', 'sample_data', (options = { sorting: false }))],
};

function init() {
    window.plausible =
        window.plausible ||
        function () {
            (window.plausible.q = window.plausible.q || []).push(arguments);
        };
    showCurrentSelect();
}

function showCurrentSelect() {
    if (window.location.hash) {
        url_hash = window.location.hash.substring(1);
        for (let key in content_functions) {
            if (url_hash == key.replace(/ /g, '_').replace(/\?/g, '').replace(/\./g, '').toLowerCase()) {
                showData(key);
                openTagWithText(url_hash);
                return;
            }
        }
        showData('basics');
    } else {
        showData('basics');
    }
}

async function loadData(data_name) {
    if (data_name in data_cache) {
        return data_cache[data_name];
    } else {
        data_cache[data_name] = await fetch('assets/' + data_name + '.json').then((response) => {
            return response.json();
        });
        return data_cache[data_name];
    }
}

async function showData(data_name) {
    document.getElementById('data').innerHTML = '';
    for (const [index, content_function] of content_functions[data_name].entries()) {
        await content_function['show']('id-' + index);
    }

    plausible('Show Data', { props: { 'Data Name:': data_name } });

    if (content_functions[data_name].some((content_function) => 'save_img' in content_function)) {
        document.getElementById('saveImgBtn').onclick = async function () {
            for (const [index, content_function] of content_functions[data_name].entries()) {
                if ('save_img' in content_function) {
                    content_function['save_img']('id-' + index);
                }
            }
            plausible('Downloaded Image', { props: { 'Data Name:': data_name } });
        };
        document.getElementById('saveImgBtn').style.display = '';
    } else {
        document.getElementById('saveImgBtn').style.display = 'none';
    }

    if (content_functions[data_name].some((content_function) => 'save_data' in content_function)) {
        document.getElementById('saveDataBtn').onclick = async function () {
            for (const [index, content_function] of content_functions[data_name].entries()) {
                if ('save_data' in content_function) {
                    content_function['save_data']('id-' + index);
                }
            }
            plausible('Downloaded Data', { props: { 'Data Name:': data_name } });
        };
        document.getElementById('saveDataBtn').style.display = '';
    } else {
        document.getElementById('saveDataBtn').style.display = 'none';
    }

    history.replaceState(
        null,
        '',
        '#' + data_name.replace(/ /g, '_').replace(/\?/g, '').replace(/\./g, '').toLowerCase(),
    );
}

function getPlotConfig() {
    return { displayModeBar: false, staticPlot: screen.width < 850, responsive: true };
}

function getPlotLayout() {
    return {
        font: { family: 'Times', size: '15' },
        paper_bgcolor: '#dfdfdf',
        plot_bgcolor: '#dfdfdf',
    };
}

function getLinePlotLayout(plot_title, x_unit, y_unit, percent, bar_chart_on_top_of_each_other) {
    layout = Object.assign({}, getPlotLayout(), {
        margin: { l: 55, r: 55, b: 55, t: 55 },
        title: { text: plot_title },
        xaxis: { title: { text: x_unit } },
        yaxis: { title: { text: y_unit }, rangemode: 'tozero' },
    });
    if (percent) {
        layout['yaxis']['range'] = [0, 101];
    }
    if (bar_chart_on_top_of_each_other) {
        layout['barmode'] = 'stack';
    }
    return layout;
}

function hoursToStr(hours) {
    if (hours >= 10) {
        return Math.round(hours) + 'h';
    } else {
        return Math.floor(hours) + ':' + String(Math.round((hours % 1) * 60)).padStart(2, '0') + 'h';
    }
}

function selectTickInterval(maxTime) {
    const intervals = [1, 2, 5, 10, 15, 20, 30, 60]; // Potential intervals in minutes
    const maxTimeInMinutes = maxTime * 60;

    for (let interval of intervals) {
        if (maxTimeInMinutes / interval <= 7) {
            return interval; // Return interval in minutes
        }
    }
    return 60; // Default to 60 minutes (or 1 hour) if maxTime is very large
}

function addSingleLinePlot(plot_title, data_name, options = {}) {
    const default_options = {
        x_column_name: undefined,
        y_column_name: undefined,
        percent: false,
        y_hour: false,
        y_minute: false,
        type: 'bar',
        y_axis_year: false,
    };
    const opt = Object.assign({}, default_options, options);
    show_content = async function (div_id) {
        data = await loadData(data_name);
        if (opt.x_column_name == undefined) {
            opt.x_column_name = data['columns'][0];
        }
        if (opt.y_column_name == undefined) {
            opt.y_column_name = data['columns'][1];
        }

        if (opt.percent) {
            y_unit = '%';
        } else {
            y_unit = opt.y_column_name;
        }

        div = addDiv(div_id, 'dataDiv');
        const x = data['data'].map((tuple) => tuple[data['columns'].indexOf(opt.x_column_name)]);
        const y = data['data'].map((tuple) => tuple[data['columns'].indexOf(opt.y_column_name)]);

        traces = [{ x: x, y: y, type: opt.type, name: '', hovertemplate: '%{x}<br>%{y:,} ' + y_unit }];
        layout = getLinePlotLayout(plot_title, opt.x_column_name, y_unit, opt.percent);
        if (opt.y_axis_year) {
            layout['xaxis']['type'] = 'category';
            layout['xaxis']['dtick'] = 1;
        }
        if (opt.y_hour || opt.y_minute) {
            const maxTime = Math.max(...y); // Finding the maximum time
            const tickInterval = selectTickInterval(maxTime); // Get adaptive tick interval

            let tickvals = [];
            let ticktext = [];
            for (let i = 0; i <= maxTime * 60 + tickInterval; i += tickInterval) {
                const hours = Math.floor(i / 60);
                const minutes = i % 60;

                tickvals.push(i / 60); // Convert i back to hours for tickvals
                ticktext.push(`${String(hours).padStart(1, '0')}:${String(minutes).padStart(2, '0')}`);
            }

            layout['yaxis']['tickvals'] = tickvals;
            layout['yaxis']['ticktext'] = ticktext;

            traces[0]['hovertext'] = y.map((value) => {
                const hours = Math.floor(value);
                const minutes = Math.round((value - hours) * 60);
                return `${String(hours).padStart(1, '0')}:${String(minutes).padStart(2, '0')}`;
            });

            traces[0]['hovertemplate'] = '%{x}<br>%{hovertext}';
        }
        Plotly.newPlot(div, traces, layout, getPlotConfig());
    };
    return {
        show: show_content,
        save_img: async function (div_id) {
            savePlot(data_name, div_id);
        },
        save_data: async function () {
            saveData(data_name);
        },
    };
}

function addDiv(id, class_str, parent_div = null) {
    let div = document.createElement('div');
    div.id = String(id);
    div.style.display = 'inline-block';
    div.classList.add(class_str);
    if (parent_div == null) {
        document.getElementById('data').appendChild(div);
    } else {
        parent_div.appendChild(div);
    }
    return div;
}

function addMultiLinePlot(plot_title, data_name, y_unit, options = {}) {
    const default_options = {
        x_column_name: undefined,
        y_column_names: undefined,
        percent: false,
        stacked: false,
        bar_chart: true,
        reverse_y_names: false,
    };
    const opt = Object.assign({}, default_options, options);

    show_content = async function (div_id) {
        data = await loadData(data_name);
        if (opt.x_column_name == undefined) {
            opt.x_column_name = data['columns'][0];
        }
        if (opt.y_column_names == undefined) {
            opt.y_column_names = data['columns'].slice(1);
        }

        const x = data['data'].map((tuple) => tuple[data['columns'].indexOf(opt.x_column_name)]);
        div = addDiv(div_id, 'dataDiv');
        traces = [];
        for (y_column_name of opt.y_column_names) {
            const y = data['data'].map((tuple) => tuple[data['columns'].indexOf(y_column_name)]);
            trace = {
                x: x,
                y: y,
                mode: 'lines',
                name: y_column_name.replaceAll(' by ', ' by<br>'),
                hovertemplate: '%{x}<br>%{y:,} ' + y_unit,
            };
            if (opt.stacked) {
                trace['stackgroup'] = 'one';
            }
            if (opt.bar_chart) {
                trace['type'] = 'bar';
            }
            if (opt.reverse_y_names) {
                traces.unshift(trace);
            } else {
                traces.push(trace);
            }
        }

        const bar_chart_stacked = opt.bar_chart && opt.stacked;
        Plotly.newPlot(
            div,
            traces,
            getLinePlotLayout(plot_title, opt.x_column_name, y_unit, opt.percent, bar_chart_stacked),
            getPlotConfig(),
        );
    };
    return {
        show: show_content,
        save_img: async function (div_id) {
            savePlot(data_name, div_id);
        },
        save_data: async function () {
            saveData(data_name);
        },
    };
}

async function savePlot(data_name, div_id) {
    await Plotly.toImage(document.getElementById(div_id), { format: 'png', height: 500, width: 1000 }).then(
        function (png_str) {
            download(png_str, data_name, 'png');
        },
    );
}

async function saveData(data_name) {
    data = await loadData(data_name);
    download(data, data_name, 'json');
}

function addText(text, data_name = null) {
    show_content = async function (div_id) {
        div = addDiv(div_id, 'textDiv');
        temp_text = text;
        if (displayUserData) {
            temp_text = changeTextFromIToYou(temp_text);
        }
        if (data_name !== null) {
            replaceValueDict = data_cache[data_name];
            for (let key in replaceValueDict) {
                let pattern = new RegExp(`{${key}}`, 'g');
                value = replaceValueDict[key];
                if (typeof value == 'number') {
                    value = value.toLocaleString('en-US');
                }
                temp_text = temp_text.replace(pattern, value);
            }
        }
        div.insertAdjacentHTML('beforeend', temp_text);
    };
    out = { show: show_content };
    if (data_name !== null) {
        out['save_data'] = async function () {
            saveData(data_name);
        };
    }
    return out;
}

function downloadTableAsImage(div_id, data_name) {
    // Check if HTML2Canvas is already loaded
    if (typeof html2canvas === 'undefined') {
        // Create a script element to load HTML2Canvas
        var script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
        script.onload = function () {
            captureTable(div_id, data_name);
        };
        document.head.appendChild(script);
    } else {
        captureTable(div_id, data_name);
    }
}

function captureTable(div_id, data_name) {
    const table = document.getElementById(div_id).querySelector('table');
    // Use HTML2Canvas to capture the table
    html2canvas(table, { scale: 2 }) // Change the scale value to control the resolution
        .then(function (canvas) {
            var link = document.createElement('a');
            link.href = canvas.toDataURL();
            link.download = data_name + '.png';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
}

function addTableRowWise(title, data_name, options = {}) {
    show_content = async function (div_id) {
        data = await loadData(data_name);
        div = addDiv(div_id, 'dataDiv');
        div.style.width = '100%';
        div.style.aspectRatio = 'auto';
        div.innerHTML = getTableHtmlRowWise(title, data, options);
    };

    return {
        show: show_content,
        save_img: async function (div_id) {
            downloadTableAsImage(div_id, data_name);
        },
        save_data: async function () {
            saveData(data_name);
        },
    };
}

function getTableHtmlRowWise(title, data, options) {
    const default_options = {
        show_rank: false,
        sorting: true,
        columns_without_sorting: ['monthly play count'],
    };
    const opt = Object.assign({}, default_options, options);

    let head_entries = [];
    if (opt.show_rank) {
        head_entries.push('rank');
    }
    head_entries = head_entries.concat(data.columns);

    let head = '<tr>';
    for (var i in head_entries) {
        if (opt.sorting & !opt.columns_without_sorting.includes(head_entries[i])) {
            head += '<th class="sorting" onclick="sortTable(event)">' + head_entries[i] + '</th>';
        } else {
            head += '<th>' + head_entries[i] + '</th>';
        }
    }
    head += '</tr>';

    let body = '';
    let rank = 1;
    for (let row_index in data.data) {
        body += '<tr>';
        if (opt.show_rank) {
            body += '<td>' + String(rank) + '</td>';
            rank += 1;
        }
        for (column_index in data.data[row_index]) {
            let y_value = data.data[row_index][column_index];
            if (typeof y_value == 'number') {
                if (data.columns[column_index] == 'hours played') {
                    y_value = hoursToStr(y_value);
                } else {
                    y_value = y_value.toLocaleString('en-US');
                }
            } else if (typeof y_value == 'string') {
                if (y_value.slice(0, 22) == 'data:image/bmp;base64,') {
                    y_value = '<img src="' + y_value + '">';
                }
            }
            body += '<td>' + y_value + '</td>';
        }
    }
    return '<h3>' + title + "</h3><table style='margin: 0 auto;'>" + head + body + '</table>';
}

async function sortTable(e) {
    for (var child = e.srcElement.parentElement.firstChild.nextSibling; child !== null; child = child.nextSibling) {
        if (child != e.srcElement && !child.classList.contains('sorting')) {
            child.classList.remove('sortingAsc', 'sortingDesc');
            child.classList.add('sorting');
        }
    }

    if (e.srcElement.classList.contains('sorting')) {
        e.srcElement.classList.remove('sorting');
        e.srcElement.classList.add('sortingAsc');
    } else if (e.srcElement.classList.contains('sortingAsc')) {
        e.srcElement.classList.remove('sortingAsc');
        e.srcElement.classList.add('sortingDesc');
    } else {
        e.srcElement.classList.remove('sortingDesc');
        e.srcElement.classList.add('sortingAsc');
    }

    const parseHours = (value) => {
        if (value.includes('h')) {
            const parts = value.split(':');
            const hours = parseInt(parts[0]);
            const minutes = parts.length > 1 ? parseInt(parts[1].replace('h', '')) : 0;
            return hours + minutes / 60;
        }
        return value;
    };

    const getCellValue = (tr, idx, shouldParseHours) => {
        const rawValue =
            tr.children[idx].innerText.replaceAll(',', '') || tr.children[idx].textContent.replaceAll(',', '');
        return shouldParseHours ? parseHours(rawValue) : rawValue;
    };

    const th = e.srcElement;
    const ascending = !th.classList.contains('sortingAsc') || th.classList.contains('sortingDesc');
    const table = th.closest('table');
    const headerText = th.innerText.trim();
    const shouldParseHours = headerText === 'hours played';

    const comparer = (idx, asc) => (a, b) =>
        ((v1, v2) => (v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2)))(
            getCellValue(asc ? a : b, idx, shouldParseHours),
            getCellValue(asc ? b : a, idx, shouldParseHours),
        );

    Array.from(table.querySelectorAll('tr:nth-child(n+2)'))
        .sort(comparer(Array.from(th.parentNode.children).indexOf(th), ascending))
        .forEach((tr) => table.appendChild(tr));
}

async function processUserData() {
    let reader = new FileReader();
    reader.onload = async function (event) {
        document.getElementById('data').style.display = 'none';
        document.getElementById('progressText').style.display = '';
        document.getElementById('progressText').innerHTML =
            'Processing your spotify data. This can take one to two minutes.</br></br>';

        updateProgress('1/9: loading pyodide and pandas', false);
        const module = await import('https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js');
        pyodide = await loadPyodide({ packages: ['pandas'] });

        const data = new Uint8Array(event.target.result);
        pyodide.globals.set('data', data);

        updateProgress('2/9: loading and starting code');
        const response = await fetch('data_crunching.py');
        const pythonCode = await response.text();
        await pyodide.runPythonAsync(pythonCode);

        updateProgress('3/9: loading zip file');
        const filenames_py = await pyodide.runPythonAsync(`
            import zipfile
            zip_ref = zipfile.ZipFile(BytesIO(bytes(list(data))), "r")
            filenames = [fn for fn in zip_ref.namelist() if fn.endswith(".json")]
            filenames
        `);

        const filenames = filenames_py.toJs();
        // check if "Technical log information" is uploaded instead of the "Extended streaming history".
        if (
            filenames.includes('MyData/share.json') ||
            filenames.includes('MyData/AddedToCollection.json') ||
            filenames.includes('MyData/Download_Hourly.json')
        ) {
            updateProgress(
                'Error: It seems like you added your "technical log information" instead of your "Extended streaming history". It could be that download link of your "Extended streaming history" from spotify takes a little longer.',
            );
            return;
        }
        // check if "account data" is uploaded instead of the "Extended streaming history".
        if (filenames.includes('MyData/YourLibrary.json') || filenames.includes('MyData/Userdata.json')) {
            updateProgress(
                'Error: It seems like you added your "account data" instead of your "Extended streaming history". It could be that download link of your "Extended streaming history" from spotify takes a little longer.',
            );
            return;
        }

        updateProgress('4/9: reading json files in zip');
        await pyodide.runPythonAsync(`
            from io import StringIO
            df_list = []
            for i, name in enumerate(filenames):
                df_list.append(read_json(StringIO(zip_ref.read(name).decode("utf-8"))))
            zip_ref.close()
        `);
        updateProgress('5/9: creating database');
        await pyodide.runPythonAsync('df = pd.concat(df_list)');

        updateProgress('6/9: preprocessing data');
        await pyodide.runPythonAsync(`
            df = preprocess_df(df)
            original_df = df
            top_k = 20
        `);

        updateProgress('7/9: generate table and plot data');
        await pyodide.runPythonAsync('df_dict = get_df_dict(df, top_k)');

        updateProgress('8/9: postprocess table and plot data');
        await pyodide.runPythonAsync('post_process_dataframe_dict(df_dict)');

        updateProgress('9/9: save table and plot data as json');
        let returns = await pyodide.runPythonAsync(`
            single_values = get_single_values(df, df_dict)
            df_dict_to_df_json_dict(df_dict)

            {"df_dict": df_dict, "single_values": single_values}
        `);
        updateProgress('read table and plot data in js');

        data_cache = Object.fromEntries([...returns.get('df_dict').toJs()].map(([k, v]) => [k, Object.fromEntries(v)]));
        data_cache['basics_dict'] = Object.fromEntries(returns.get('single_values').toJs());

        updateProgress('finished');
        document.getElementById('filterDataBoxButton').style.display = '';
        document.getElementById('randomSampleButton').style.display = '';
        document.getElementById('downloadDFButton').style.display = '';

        displayUserData = true;
        var textDiv = document.getElementById('introductionText');
        textDiv.innerHTML = changeTextFromIToYou(textDiv.innerHTML);

        showCurrentSelect();
        document.getElementById('data').style.display = '';
        document.getElementById('progressText').style.display = 'none';
        plausible('Uploaded Data');

        populateFilterData();
    };

    reader.onerror = function (event) {
        updateProgress('Error reading file:', event);
        return;
    };

    reader.readAsArrayBuffer(document.getElementById('zipFile').files[0]);
}

function updateProgress(text, addDone = true) {
    if (addDone) {
        document.getElementById('progressText').innerHTML += ' Done</br>';
    }
    document.getElementById('progressText').innerHTML += text + '...';
}

function changeTextFromIToYou(text) {
    text = text.replace(/\. I\b/g, '. You');
    text = text.replace(/<li>I\b/g, '<li>You');
    text = text.replace(/\bI\b/g, 'you');
    text = text.replace(/\bMy\b/g, 'Your');
    text = text.replace(/\bmy\b/g, 'your');
    return text;
}

async function getRandomSample(event) {
    openTab(event);
    const returns = await pyodide.runPythonAsync('get_df_random_sample(df, sample_count=1)');
    data_cache['sample_data'] = Object.fromEntries(returns.toJs());
    showData('sample_data');
}

async function downloadDF() {
    const csv_string = await pyodide.runPythonAsync(`
        buffer = StringIO()
        df.to_csv(buffer, index=False)
        buffer.getvalue()
    `);
    download(csv_string, 'streaming_history', 'csv');
}

function download(data_str, title, file_ending) {
    const downloadLink = document.createElement('a');
    downloadLink.download = title + '.' + file_ending;
    if (file_ending == 'csv') {
        data_str = window.URL.createObjectURL(new Blob([data_str], { type: 'text/csv' }));
    } else if (file_ending == 'json') {
        data_str = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(data_str));
    }
    downloadLink.href = data_str;
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

async function populateFilterData() {
    await pyodide.runPythonAsync(`
        min_year_month = df["year_month"].min().split("-")
        min_year = int(min_year_month[0])
        min_month = int(min_year_month[1])
        max_year_month = df["year_month"].max().split("-")
        max_year = int(max_year_month[0])
        max_month = int(max_year_month[1])
    `);

    const minYear = pyodide.globals.get('min_year');
    const minMonth = pyodide.globals.get('min_month');
    const maxYear = pyodide.globals.get('max_year');
    const maxMonth = pyodide.globals.get('max_month');
    let startDateSelect = document.getElementById('startDate');
    let endDateSelect = document.getElementById('endDate');

    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    for (let year = minYear; year <= maxYear; year++) {
        let startMonthBound = year === minYear ? minMonth : 1;
        let endMonthBound = year === maxYear ? maxMonth : 12;

        for (let month = startMonthBound; month <= endMonthBound; month++) {
            let optionValue = `${year}-${month}`;
            let optionText = `${year}-${months[month - 1]}`;
            startDateSelect.options.add(new Option(optionText, optionValue));
            endDateSelect.options.add(new Option(optionText, optionValue));
        }
    }

    endDateSelect.selectedIndex = endDateSelect.options.length - 1;
}

async function filterData() {
    const startDateSelect = document.getElementById('startDate');
    const min_year_month = startDateSelect.options[startDateSelect.selectedIndex].value;
    pyodide.globals.set('min_year', parseInt(min_year_month.split('-')[0]));
    pyodide.globals.set('min_month', parseInt(min_year_month.split('-')[1]));

    const endDateSelect = document.getElementById('endDate');
    const max_year_month = endDateSelect.options[endDateSelect.selectedIndex].value;
    pyodide.globals.set('max_year', parseInt(max_year_month.split('-')[0]));
    pyodide.globals.set('max_month', parseInt(max_year_month.split('-')[1]));

    pyodide.globals.set('artist_name', document.getElementById('artistName').value.trim());

    const select = document.getElementById('changeTopKSelect');
    const topKText = select.options[select.selectedIndex].text;
    if (topKText.includes('-')) {
        topK = parseInt(topKText.split('-')[1]);
    } else {
        topK = 100000;
    }
    pyodide.globals.set('top_k', topK);

    document.getElementById('data').innerHTML = 'Loading';

    const returns = await pyodide.runPythonAsync(`
        df = original_df[(
            ((original_df['year'] > min_year) | 
            ((original_df['year'] == min_year) & (original_df['month'] >= min_month))) &
            ((original_df['year'] < max_year) |
            ((original_df['year'] == max_year) & (original_df['month'] <= max_month)))
        )]
        if artist_name != "":
            df = df[df['artist'] == artist_name]
        
        if len(df[df["full_play"]]) > 0:
            df_dict = get_df_dict(df, top_k=top_k)
            post_process_dataframe_dict(df_dict)
            single_values = get_single_values(df, df_dict)
            df_dict_to_df_json_dict(df_dict)
            out = {"df_dict": df_dict, "single_values": single_values}
        else:
            out = {"error": "No plays from this artist in this time frame."}

        out
    `);

    if (returns.has('error')) {
        document.getElementById('data').innerHTML = returns.get('error');
    } else {
        data_cache = Object.fromEntries([...returns.get('df_dict').toJs()].map(([k, v]) => [k, Object.fromEntries(v)]));
        data_cache['basics_dict'] = Object.fromEntries(returns.get('single_values').toJs());
        showCurrentSelect();
    }
}

function toggleBox(elementId) {
    const box = document.getElementById(elementId);
    if (box.style.display === 'none' || box.style.display === '') {
        box.style.display = 'block';
    } else {
        box.style.display = 'none';
    }
}

function openTagWithText(targetText) {
    let tablinks = document.getElementsByClassName('tablinks');
    for (let i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(' active', '');
        let tabText = tablinks[i].innerText.replace(/ /g, '_').replace(/\?/g, '').replace(/\./g, '').toLowerCase();
        if (tabText == targetText) {
            tablinks[i].className += ' active';
        }
    }
}

function openTab(event) {
    let tablinks = document.getElementsByClassName('tablinks');
    for (let i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(' active', '');
    }
    event.currentTarget.className += ' active';
}

function openTabShowData(event) {
    openTab(event);
    const dataName = event.target.textContent || event.target.innerText;
    showData(dataName);
}
