# coding: utf-8
import json
from pathlib import Path


# start with this JSON, which is a find-replace from the homepage
# https://imsdb.com/all-scripts.html
def parse_01():
    metadata = json.loads(Path("data/metadata/IMSDb-2021-10-26.json").read_text())

    # fix writers
    for script in metadata:
        script["writers"] = script["writers"].split(",")

    # get year-month and status
    for script in metadata:
        if "Undated" in script["date"]:
            script["year_month"] = None
            script["status"] = script["date"][8:]
        else:
            if ("Draft" in script["date"] and len(script["date"]) == 10) or (
                "Transcript" in script["date"] and len(script["date"]) == 15
            ):
                script["year_month"] = script["date"][:4]
                script["status"] = script["date"][5:]
            else:
                script["year_month"] = script["date"][:7]
                script["status"] = script["date"][8:]


    # check on statuses
    set([script["status"] for script in metadata])

    # save the file
    Path("data/metadata/IMSDb-2021-10-26-parsed-01.json").write_text(json.dumps(metadata, indent=4))
    print(
        "cleaned up caps mismatch on status, and two movie statuses: godzilla, evil dead; by hand."
    )

def parse_02():
    metadata = json.loads(Path("data/metadata/IMSDb-2021-10-26-parsed-01.json").read_text())
    for script in metadata:
        if script['title'][-5:] == ", The":
            script['html_filename'] = 'The ' + script['title'][:-5]
        # elif script['title'][-3:] == ", A":
        #     script['html_filename'] = 'A ' + script['title'][:-3]
        elif script['title'] == "Avventura, L' (The Adventure)":
            script['html_filename'] = "L' Avventura (The Adventure)"
        elif script['title'] == "After.Life":
            script['html_filename'] = "After Life"
        elif script['title'] == "Majestic, The (The Bijou)":
            script['html_filename'] = "The Majestic (The Bijou)"
        else:
            script['html_filename'] = script['title']
        script['html_filename'] = (
            script['html_filename']
                .replace(' ', '-')
                .replace(':', '')
                .replace('.', '')
                .replace('&amp;', '&')
                .replace('\'', '')
                .replace('---', '-')
                .replace('?', '')
        )
    Path("data/metadata/IMSDb-2021-10-26-parsed-02.json").write_text(json.dumps(metadata, indent=4))


def check_html_files_in_metadata():
    scripts = json.loads(Path("data/metadata/IMSDb-2021-10-26-parsed-02.json").read_text())
    filenames = [script.stem for script in  Path('data/scripts/html').iterdir()]
    all_titles = [script['html_filename'] for script in scripts]

    for filename in filenames:
        if filename not in all_titles:
            print(filename)


if __name__ == "__main__":
    # parse_01()
    parse_02()
    check_html_files_in_metadata()