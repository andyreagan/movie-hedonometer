# chop.py
#
# chop up a text into a bunch of frequency vectors of length
#
# USAGE
#
# python chop.py data/count-of-monte-cristo.txt output french

import codecs  # handle utf8
import datetime
import os
import re
import shutil
import sys
from pathlib import Path

from labMTsimple.storyLab import *
from numpy import array, floor, zeros
from tqdm import tqdm

sys.path.append("/home/prod/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
from django.conf import settings
from hedonometer.models import Movie
from labMTsimple.speedy import *

labMTsenti = sentiDict("LabMT", stopVal=0.0)

# assume everything is in english
lang = "english"
labMT, labMTvector, labMTwordList = emotionFileReader(
    stopval=0.0, lang=lang, returnVector=True
)

DATA_PATH = Path('data')


def chopper(words, labMT, labMTvector, outfile: Path, minSize: int=1000) -> None:
    # print("now splitting the text into chunks of size 1000")
    # print("and printing those frequency vectors")
    allFvec = []
    from numpy import floor

    for i in range(int(floor(len(words) / minSize))):
        chunk = unicode("")
        if i == int(floor(len(words) / minSize)) - 1:
            # take the rest
            # print('last chunk')
            # print('getting words ' + str(i*minSize) + ' through ' + str(len(words)-1))
            for j in range(i * minSize, len(words) - 1):
                chunk += words[j] + unicode(" ")
        else:
            # print('getting words ' + str(i*minSize) + ' through ' + str((i+1)*minSize))
            for j in range(i * minSize, (i + 1) * minSize):
                chunk += words[j] + unicode(" ")
                # print(chunk[0:10])
        textValence, textFvec = emotion(chunk, labMT, shift=True, happsList=labMTvector)
        # print(chunk)
        # print('the valence of {0} part {1} is {2}'.format(rawbook,i,textValence))
        allFvec.append(textFvec)

    f = open(outfile,"w")
    if len(allFvec) > 0:
        print "writing out the file to {0}".format(outfile)
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
        print('"' * 40)
        print(f"not saving {outfile}, len(allFvec) == {len(allFvec)}")
        print('"' * 40)


def precomputeTimeseries(fullVec, labMT, labMTvector, outfile: Path) -> None:
    minWindows = 10
    timeseries = [0 for i in range(len(fullVec[0]) + 1)]
    # print(len(timeseries))

    textFvec = [0 for j in range(len(fullVec))]
    for i in range(0, minWindows / 2):
        textFvec = [textFvec[j] + fullVec[j][i] for j in range(len(fullVec))]
        # print("adding point {0}".format(i))

    for i in range(minWindows / 2, minWindows):
        # print("scoring")
        stoppedVec = stopper(textFvec, labMTvector, labMTwordList, stopVal=2.0)
        timeseries[i - minWindows / 2] = emotionV(stoppedVec, labMTvector)
        # print("adding point {0}".format(i))
        textFvec = [textFvec[j] + fullVec[j][i] for j in range(len(fullVec))]

    for i in range(minWindows, len(timeseries) - 1):
        # print("scoring")
        stoppedVec = stopper(textFvec, labMTvector, labMTwordList, stopVal=2.0)
        timeseries[i - minWindows / 2] = emotionV(stoppedVec, labMTvector)
        # print("adding point {0}".format(i))
        # print("removing point {0}".format(i-minWindows))
        textFvec = [
            textFvec[j] + fullVec[j][i] - fullVec[j][i - minWindows]
            for j in range(len(fullVec))
        ]

    for i in range(len(timeseries) - 1, len(timeseries) + minWindows / 2):
        # print("scoring")
        stoppedVec = stopper(textFvec, labMTvector, labMTwordList, stopVal=2.0)
        timeseries[i - minWindows / 2] = emotionV(stoppedVec, labMTvector)
        # print("removing point {0}".format(i-minWindows))
        textFvec = [
            textFvec[j] - fullVec[j][i - minWindows] for j in range(len(fullVec))
        ]

    # print("done")
    # print(timeseries[0:11])
    # print(timeseries[-11:])

    outfile.write_text(",".join(["{0}".format(x) for x in timeseries]))


def process(windowSizes: list = [2000], updateModel: bool=False) -> None:
    # windowSizes = [500,1000,2000,5000,10000]

    # script_path = DATA_PATH / Path("scripts/scriptsClean")
    script_path = DATA_PATH / Path("scripts/html-cleaned")


    for movie in tqdm(movies):
        print("filename:")
        print(movie.filename)

        print("titleraw:")
        print(movie.titleraw)

        filename = Path(movie.titleraw.replace(" ", "-").replace(".", "-") + ".txt")
        full_path = (script_path / filename)

        if full_path.exists():
            print("found file for title:")
            print(movie.title)

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
            print("length of the original parse")
            print(len(words))
            print("length of the new parse")
            print(len(kwords))
            # print(len(klines))
            # print(klines[0:20])

            for window in windowSizes:
                print(window)
                window_path = DATA_PATH / Path("word-vectors") / Path(str(window))

                # print(klines[0:(window/10)])
                breaks = [
                    klines[window / 10 * i]
                    for i in range(int(floor(float(len(klines)) / window * 10)))
                ]
                breaks[0] = 0
                # print([window/10*i for i in range(int(floor(float(len(klines))/window*10)))])
                # print(breaks)
                # print(len(breaks))

                breaks_filename = Path(movie.filename + "-breaks.csv")
                breaks_file = window_path / output_filename
                breaks_file.write_text(",".join(map(str, breaks)))

                chopped_file = window_path / Path(movie.filename + ".csv"),

                chopper(
                    kwords,
                    labMT,
                    labMTvector,
                    chopped_file,
                    minSize=window / 10,
                )

                f = chopped_file.read_text()
                fullVec = [map(int, line.split(",")) for line in f.split("\n")]

                timeseries_path = DATA_PATH / Path("timeseries") / Path(str(window))
                timeseries_filename = movie.filename + ".csv"
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
                    print("this movie is blank:")
                    print(movie.title)
                    if updateModel:
                        movie.exclude = True
                        movie.excludeReason = "movie blank"
                        movie.save()

        else:
            print("movie does not have a file at:")
            print(full_path)
            if updateModel:
                movie.exclude = True
                movie.excludeReason = "missing raw file in scriptsClean"
                movie.save()


def process_overallHapps(movies) -> None:
    '''
    Read the scripts raw, generate a vector in word-vectors/full for
    each script, with the ignoreWords removed (but 4-6 still included).

    Also write one out called all.csv, for everything added up.
    '''
    alltext_dict = dict()
    alltext_labMT_fVec = zeros(10222)
    ignoreWords = ["camera", "cuts"]
    script_path = DATA_PATH / Path("scripts/html-cleaned")

    for movie in tqdm(movies):

        print("filename:")
        print(movie.filename)

        print("titleraw:")
        print(movie.titleraw)

        filename = Path(movie.titleraw.replace(" ", "-").replace(".", "-") + ".txt")
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

        print("length of the new parse")
        print(len(kwords))

        rawtext = " ".join(kwords)

        textValence, textFvec = emotion(
            rawtext, labMT, shift=True, happsList=labMTvector
        )

        # this is just going to block the four nigg* and the specific movie words
        stoppedVec = stopper(
            textFvec, labMTvector, labMTwordList, stopVal=0.0, ignore=(ignoreWords + movie.ignorewords.split(","))
        )
        # add this minimally blocked list to the total
        # (since I want to only block these special words for some movies...)
        # a bit convoluted
        alltext_labMT_fVec += stoppedVec

        (DATAPATH / Path("word-vectors/full") / Path(movie.filename + ".csv")).write_text(
            ",".join(["{0:.0f}".format(x) for x in stoppedVec]))
        )

        # fully stop the vec to compute the happiness
        stoppedVec = stopper(
            textFvec, labMTvector, labMTwordList, stopVal=2.0, ignore=ignoreWords
        )
        happs = emotionV(stoppedVec, labMTvector)
        print(happs)

        movie.length = len(kwords)
        movie.happs = happs
        movie.save()

    stoppedVec = stopper(
        alltext_labMT_fVec, labMTvector, labMTwordList, stopVal=2.0, ignore=ignoreWords
    )
    happs = emotionV(stoppedVec, labMTvector)

    # write out the word vector, not stopped except for the specific words
    (DATAPATH / Path("word-vectors/full") / Path("all.csv")).write_text(
        ",".join(["{0:.0f}".format(x) for x in alltext_labMT_fVec]))
    )


def detect_line_type(movies) -> None:
    for movie in tqdm(movies):
        m = movies[i]
        # print(m.title)
        f = codecs.open("raw/" + m.filename + ".txt.clean01", "r", "utf8")
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
                # print(bold)
                space = bold[0][0]
                bold_spacings.append(len(space))
                text = bold[0][1].rstrip(" ")
                types[i] = "l"
                # lines[i] = space+text
                continue
            line_match = re.findall(r"^([ ]*)(.*?)$", line)
            if len(line_match) > 0:
                # if i<100:
                #     print(line_match)
                space = line_match[0][0]
                general_spacings.append(len(space))
                text = line_match[0][1].rstrip(" ")
                types[i] = "a"
                # lines[i] = space+text

        # print(bold_spacings[:100])
        # print(np.mean(bold_spacings))
        # print(general_spacings[:100])
        # print(np.mean(general_spacings))
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
        f = codecs.open("raw/" + m.filename + ".script", "w", "utf8")
        f.write("\n".join([types[i].upper() + lines[i] for i in range(len(lines))]))
        f.close()



if __name__ == "__main__":
    folder = "data/scripts/html-cleaned"
    # get just one:
    # movies = Movie.objects.filter(title="127 Hours")
    movies = Movie.objects.all()

    process(movies)
    process_overallHapps(movies)
    # detect_line_type(movies)
