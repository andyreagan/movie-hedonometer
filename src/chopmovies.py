# chop.py
#
# chop up a text into a bunch of frequency vectors of length
#
# USAGE
#
# python chop.py data/count-of-monte-cristo.txt output french

import os
import re
import sys
import json
from pathlib import Path

from numpy import array, floor, zeros
from tqdm import tqdm
from labMTsimple.storyLab import *
from labMTsimple.speedy import *

# sys.path.append("/home/prod/app")
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
# from django.conf import settings
# from hedonometer.models import Movie

DATA_PATH = Path('data')
# assume everything is in english
labMT, labMTvector, labMTwordList = emotionFileReader(
    stopval=0.0, lang="english", returnVector=True
)


def chopper(words, labMT, labMTvector, outfile: Path, minSize: int=1000) -> None:
    # tqdm.write("now splitting the text into chunks of size 1000")
    # tqdm.write("and printing those frequency vectors")
    allFvec = []
    from numpy import floor

    for i in range(int(floor(len(words) / minSize))):
        chunk = ""
        if i == int(floor(len(words) / minSize)) - 1:
            # take the rest
            # tqdm.write(f'last chunk: getting words {i*minSize=} through {len(words)-1=}')
            for j in range(int(i * minSize), int(len(words) - 1)):
                chunk += words[j] + " "
        else:
            # tqdm.write(f'getting words {i*minSize=} through {(i+1)*minSize=}')
            for j in range(int(i * minSize), int((i + 1) * minSize)):
                chunk += words[j] + " "
                # tqdm.write(chunk[0:10])
        textValence, textFvec = emotion(chunk, labMT, shift=True, happsList=labMTvector)
        # tqdm.write(chunk)
        # tqdm.write('the valence of {0} part {1} is {2}'.format(rawbook,i,textValence))
        allFvec.append(textFvec)

    if len(allFvec) > 0:
        f = open(outfile, "w")
        tqdm.write(f"writing out the file to {outfile=}")
        f.write('{0:.0f}'.format(allFvec[0][0]))
        for k in range(1,len(allFvec)):
            f.write(',{0:.0f}'.format(allFvec[k][0]))
        for i in range(1,len(allFvec[0])):
            f.write("\n")
            f.write('{0:.0f}'.format(allFvec[0][i]))
            for k in range(1,len(allFvec)):
                f.write(',{0:.0f}'.format(allFvec[k][i]))
        f.close()
    else:
        tqdm.write('"' * 40)
        tqdm.write(f"not saving {outfile=}, {len(allFvec)=}")
        tqdm.write('"' * 40)


def precomputeTimeseries(fullVec, labMT, labMTvector, outfile: Path) -> None:
    minWindows = 10
    timeseries = [0 for i in range(len(fullVec[0]) + 1)]
    # tqdm.write(f'{len(timeseries)=}')

    textFvec = [0 for j in range(len(fullVec))]
    for i in range(0, int(minWindows / 2)):
        textFvec = [textFvec[j] + fullVec[j][i] for j in range(len(fullVec))]
        # tqdm.write("adding point {0}".format(i))

    for i in range(int(minWindows / 2), int(minWindows)):
        # tqdm.write("scoring")
        stoppedVec = stopper(textFvec, labMTvector, labMTwordList, stopVal=2.0)
        timeseries[int(i - minWindows / 2)] = emotionV(stoppedVec, labMTvector)
        # tqdm.write("adding point {0}".format(i))
        textFvec = [textFvec[j] + fullVec[j][i] for j in range(len(fullVec))]

    for i in range(int(minWindows), int(len(timeseries) - 1)):
        # tqdm.write("scoring")
        stoppedVec = stopper(textFvec, labMTvector, labMTwordList, stopVal=2.0)
        timeseries[int(i - minWindows / 2)] = emotionV(stoppedVec, labMTvector)
        # tqdm.write("adding point {0}".format(i))
        # tqdm.write("removing point {0}".format(i-minWindows))
        textFvec = [
            textFvec[j] + fullVec[j][i] - fullVec[j][i - minWindows]
            for j in range(len(fullVec))
        ]

    for i in range(len(timeseries) - 1, int(len(timeseries) + minWindows / 2)):
        # tqdm.write("scoring")
        stoppedVec = stopper(textFvec, labMTvector, labMTwordList, stopVal=2.0)
        timeseries[int(i - minWindows / 2)] = emotionV(stoppedVec, labMTvector)
        # tqdm.write("removing point {0}".format(i-minWindows))
        textFvec = [
            textFvec[j] - fullVec[j][i - minWindows] for j in range(len(fullVec))
        ]

    # tqdm.write("done")
    # tqdm.write(timeseries[0:11])
    # tqdm.write(timeseries[-11:])

    outfile.write_text(",".join(["{0}".format(x) for x in timeseries]))


def process(movies: list, windowSizes: list = [2000]) -> None:
    '''
    Process the cleaned up movie scripts.

    movies: list of objects that have three properties
    '''
    # windowSizes = [500,1000,2000,5000,10000]

    # script_path = DATA_PATH / Path("scripts/scriptsClean")
    script_path = DATA_PATH / Path("scripts/html-cleaned")
    for key in {"filename", "titleraw", "object"}:
        assert key in movies[0]

    for movie in tqdm(movies):
        if movie["object"] is not None:
            movie["object"].exclude = False
            movie["object"].excludeReason = ""
            movie["object"].save()
        tqdm.write(f'{movie["filename"]=}, {movie["titleraw"]=}')

        filename = Path(movie["titleraw"].replace(" ", "-").replace(".", "-") + ".txt")
        full_path = (script_path / filename)

        if full_path.exists():
            tqdm.write(f"found file for {movie['filename']=}")

            raw_text = full_path.read_text()

            words = [
                x.lower()
                for x in re.findall(
                    r"[\w\@\#\'\&\]\*\-\/\[\=\;]+", raw_text, flags=re.UNICODE
                )
            ]
            lines = raw_text.split("\n")
            kwords = []
            klines = []
            for i in range(len(lines)):
                if lines[i][0:3] != "<b>":
                    tmpwords = [
                        x.lower()
                        for x in re.findall(
                            r"[\w\@\#\'\&\]\*\-\/\[\=\;]+", lines[i], flags=re.UNICODE
                        )
                    ]
                    kwords.extend(tmpwords)
                    klines.extend([i for j in range(len(tmpwords))])

            # avhapps = emotion(raw_text,labMT)
            tqdm.write(f"length of the original parse {len(words)=}")
            tqdm.write(f"length of the new parse {len(kwords)=}")
            # tqdm.write(len(klines))
            # tqdm.write(klines[0:20])

            for window in windowSizes:
                tqdm.write(f'{window=}')
                window_path = DATA_PATH / Path("word-vectors") / Path(str(window))

                # tqdm.write(klines[0:(window/10)])
                breaks = [
                    klines[int(floor(window / 10 * i))]
                    for i in range(int(floor(float(len(klines)) / window * 10)))
                ]
                breaks[0] = 0
                # tqdm.write([window/10*i for i in range(int(floor(float(len(klines))/window*10)))])
                # tqdm.write(breaks)
                # tqdm.write(len(breaks))

                breaks_filename = Path(movie["filename"] + "-breaks.csv")
                breaks_file = window_path / breaks_filename
                breaks_file.write_text(",".join(map(str, breaks)))

                chopped_file = window_path / Path(movie["filename"] + ".csv")

                chopper(
                    kwords,
                    labMT,
                    labMTvector,
                    chopped_file,
                    minSize=window / 10,
                )

                fullVec = [list(map(int, line.split(","))) for line in chopped_file.read_text().split("\n")]

                timeseries_path = DATA_PATH / Path("timeseries") / Path(str(window))
                timeseries_filename = movie["filename"] + ".csv"
                # some movies are blank
                if len(fullVec) > 0:
                    if len(fullVec[0]) > 9:
                        precomputeTimeseries(
                            fullVec,
                            labMT,
                            labMTvector,
                            (timeseries_path / timeseries_filename)
                        )
                else:
                    tqdm.write(f'this movie is blank: {movie["titleraw"]}')
                    if movie["object"] is not None:
                        movie["object"].exclude = True
                        movie["object"].excludeReason = "movie blank"
                        movie["object"].save()

        else:
            tqdm.write(f"movie does not have a file at: {full_path=}")
            if movie["object"] is not None:
                movie["object"].exclude = True
                movie["object"].excludeReason = "missing raw file in scriptsClean"
                movie["object"].save()


def process_overallHapps(movies: list) -> None:
    '''
    Read the scripts raw, generate a vector in word-vectors/full for
    each script, with the ignoreWords removed (but 4-6 still included).

    Also write one out called all.csv, for everything added up.
    '''
    alltext_dict = dict()
    alltext_labMT_fVec = zeros(10222)
    ignoreWords = ["camera", "cuts"]
    script_path = DATA_PATH / Path("scripts/html-cleaned")

    for key in {"filename", "titleraw", "object"}:
        assert key in movies[0]

    for movie in tqdm(movies):

        tqdm.write(f'{movie["filename"]=}, {movie["titleraw"]=}')

        filename = Path(movie["titleraw"].replace(" ", "-").replace(".", "-") + ".txt")
        full_path = (script_path / filename)

        lines = full_path.read_text().split("\n")

        kwords = []
        klines = []
        for i in range(len(lines)):
            tmpwords = [
                x.lower()
                for x in re.findall(
                    r"[\w\@\#\'\&\]\*\-\/\[\=\;]+", lines[i], flags=re.UNICODE
                )
            ]
            kwords.extend(tmpwords)
            klines.extend([i for j in range(len(tmpwords))])

        tqdm.write(f"length of the new parse {len(kwords)=}")

        rawtext = " ".join(kwords)

        textValence, textFvec = emotion(
            rawtext, labMT, shift=True, happsList=labMTvector
        )

        # this is just going to block the four nigg* and the specific movie words
        stoppedVec = stopper(
            textFvec, labMTvector, labMTwordList, stopVal=0.0, ignore=(ignoreWords + movie["ignoreWords"].split(","))
        )
        # add this minimally blocked list to the total
        # (since I want to only block these special words for some movies...)
        # a bit convoluted
        alltext_labMT_fVec += stoppedVec

        (
            DATA_PATH / Path("word-vectors/full") / Path(movie["filename"] + ".csv")
        ).write_text(
                ",".join(["{0:.0f}".format(x) for x in stoppedVec])
        )

        # fully stop the vec to compute the happiness
        stoppedVec = stopper(
            textFvec, labMTvector, labMTwordList, stopVal=2.0, ignore=ignoreWords
        )
        happs = emotionV(stoppedVec, labMTvector)
        tqdm.write(f'{happs=}')

        if movie["object"] is not None:
            movie["object"].length = len(kwords)
            movie["object"].happs = happs
            movie["object"].save()

    stoppedVec = stopper(
        alltext_labMT_fVec, labMTvector, labMTwordList, stopVal=2.0, ignore=ignoreWords
    )
    happs = emotionV(stoppedVec, labMTvector)

    # write out the word vector, not stopped except for the specific words
    (
        DATA_PATH / Path("word-vectors/full") / Path("all.csv")
    ).write_text(
        ",".join(["{0:.0f}".format(x) for x in alltext_labMT_fVec])
    )


def detect_line_type(movies: list) -> None:
    for key in {"filename"}:
        assert key in movies[0]

    for movie in tqdm(movies):
        f = open(DATA_PATH / Path("scripts/html-cleaned/" + movie["filename"] + ".txt"), "r")
        script = f.read()
        f.close()
        lines = script.split("\n")
        types = ["u" for line in lines]
        line_types = {
            "u": "unknown",
            "b": "blank",
            "s": "speaker",
            "a": "action",
            "p": "speaking direction",
            "d": "dialogue",
            "l": "slug (scene)",
            "r": "right (cut to, etc)",
        }

        bold_spacings = []
        general_spacings = []
        for i, line in enumerate(lines):
            blank = re.findall(r"^[ ]*$", line)
            if len(blank) > 0:
                types[i] = "b"
                continue
            bold = re.findall(r"<b>([ ]*)([A-Z\. \-'\(\)/:0-9\#]+)</b>", line)
            if len(bold) > 0:
                # tqdm.write(bold)
                space = bold[0][0]
                bold_spacings.append(len(space))
                text = bold[0][1].rstrip(" ")
                types[i] = "l"
                # lines[i] = space+text
                continue
            line_match = re.findall(r"^([ ]*)(.*?)$", line)
            if len(line_match) > 0:
                # if i<100:
                #     tqdm.write(line_match)
                space = line_match[0][0]
                general_spacings.append(len(space))
                text = line_match[0][1].rstrip(" ")
                types[i] = "a"
                # lines[i] = space+text

        # tqdm.write(bold_spacings[:100])
        # tqdm.write(np.mean(bold_spacings))
        # tqdm.write(general_spacings[:100])
        # tqdm.write(np.mean(general_spacings))
        for i, line in enumerate(lines):
            blank = re.findall(r"^[ ]*$", line)
            if len(blank) > 0:
                types[i] = "b"
                continue
            bold = re.findall(r"<b>([ ]*)([A-Z\. \-'\(\)/:0-9\#]+)</b>", line)
            if len(bold) > 0:
                space = bold[0][0]
                # this makes it a speaker
                if len(space) > np.mean(bold_spacings):
                    types[i] = "s"
                text = bold[0][1].rstrip(" ")
                lines[i] = space + text
                continue
            line_match = re.findall(r"^([ ]*)(.*?)$", line)
            if len(line_match) > 0:
                space = line_match[0][0]
                if len(space) > np.mean(general_spacings):
                    types[i] = "d"
        f = open(DATA_PATH / Path("scripts/html-cleaned/" + movie["filename"] + ".script"), "w")
        f.write("\n".join([types[i].upper() + lines[i] for i in range(len(lines))]))
        f.close()



if __name__ == "__main__":
    # get just one:
    # movie_objects = Movie.objects.filter(title="127 Hours")
    # movie_objects = Movie.objects.all()
    # movies = [{"object": movie, "filename": movie.filename, "titleraw": movie.titleraw, "ignoreWords": movie.ignorewords} for movie in movie_objects]
    imsdb_metadata = json.loads(Path("data/metadata/IMSDb-2021-10-26-parsed-02.json").read_text())
    movies = [{"filename": movie["html_filename"], "titleraw": movie["html_filename"], "object": None, "ignoreWords": ""} for movie in imsdb_metadata][:3]

    process(movies)
    process_overallHapps(movies)
    # detect_line_type(movies)
