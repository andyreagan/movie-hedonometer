# coding: utf-8
import json
from pathlib import Path

# start with this JSON, which is a find-replace from the homepage
# https://imsdb.com/all-scripts.html
def main():
    metadata = json.loads(Path('IMSDb-2021-10-26.json').read_text())

    # fix writers
    for item in metadata:
        item['writers'] = item['writers'].split(',')

    # get year-month and status
    for item in metadata:
        if 'Undated' in item['date']:
            item['year_month'] = None
            item['status'] = item['date'][8:]
        else:
            if ('Draft' in item['date'] and len(item['date']) == 10) or ('Transcript' in item['date'] and len(item['date']) == 15):
                item['year_month'] = item['date'][:4]
                item['status'] = item['date'][5:]
            else:
                item['year_month'] = item['date'][:7]
                item['status'] = item['date'][8:]

    # check on statuses
    set([item['status'] for item in metadata])

    # save the file
    Path('IMSDb-2021-10-26-parsed.json').write_text(json.dumps(metadata, indent=4))
    print("cleaned up caps mismatch on status, and two movie statuses: godzilla, evil dead; by hand.")

if __name__ == '__main__':
    main()