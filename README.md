Moviedata processing
=========

Step 1: IMSDb metadata
------

Get a full listing of the scripts by downloading the HTML page listing all movie scripts.
My copy of this is in `data/metadata/All-Movie-Scripts-at-IMSDb.html`.

By hand, I turned this HTML file into a JSON using a text editor.
You can see that at `data/metadata/IMSDb-2021-10-26.json`.

Next, using the script at `src/imsdb-metadata/IMSDb-metadata-2021-10-26-parse.py`
we turn the JSON file into two progressively cleaner versions.
In addition, this scripts checks that the JSON listing contains all of the HTML movie scripts that we had previously downloaded.

Step 2: Get IMSDb scripts
------

For each movie listed in the JSON,
download the raw html page with the script in it to
`data/scripts/html`.

Step 3: Clean up scripts
------

Using `src/html-to-txt/clean_bs4.py` we take the raw html into text files.
We do this by extracting the script itself from the surrounding HTML using a Python library called BS4.
This library, BS4, radically simplifies the processing step.
As you can see in the script, we attempt to account for multiple ways that the
raw script is embedded into the HTML file.

This step creates all of the files in `data/scripts/html-cleaned`.

Step 4: Scripts to emotional arcs
------

Using `src/chopmovies.py` we "chop" the raw text into words,
and generate the timeseries and word vectors that power the online viewer.

This populates both `src/timeseries` and `src/word-vectors`.

Optional: Get metadata from IMDB
------

The Hedonometer website's database is populated from IMDB entries from the movies using a API from mashape (an API provider).
The scripts to do this are kept in `src/imdb-metadata`.

