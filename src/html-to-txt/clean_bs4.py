from pathlib import Path
import re

from bs4 import BeautifulSoup
from tqdm import tqdm


def main():
    filenames = [script.stem for script in  Path('data/scripts/html').iterdir()]
    for filename in tqdm(filenames):
        soup = BeautifulSoup((Path('data/scripts/html') / Path(filename + '.html')).read_text(), 'html.parser')
        tables = [table for table in soup.find_all('td') if (table.get('class') is not None and table.get('class')[0] == 'scrtext')]
        if len(tables) == 1:
            table = tables[0]
            # print('found it')
            # print(len(table.get_text()))
            if len(table.get_text()) < 10000:
                print(f'{filename} found it, but too short: {len(table.get_text())}')
            text = table.get_text()
            if len(text.split('\n')) < 100:
                text = re.sub("(\s{10,})", "\n\\1", text)
            (Path('data/scripts/html-cleaned') / Path(filename + '.txt')).write_text(text)
        else:
            print(f'{filename}: did not find the source, found {len(tables)} sources')

if __name__ == '__main__':
    main()