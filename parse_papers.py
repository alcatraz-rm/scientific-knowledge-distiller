import json
import os
import pprint
from pathlib import Path
from pprint import pprint

from science_parse_api.api import parse_pdf

to_ignore = ['.DS_Store']
papers_paths = os.listdir('papers')

host = 'http://127.0.0.1'
port = '8080'

for file in to_ignore:
    if file in papers_paths:
        papers_paths.remove(file)

citations = []

with open('papers_data.json', 'r', encoding='utf-8') as file:
    metadata = json.load(file)

for path_to_paper in papers_paths:
    print(path_to_paper)

    parsed_pdf = parse_pdf(host, Path(os.path.join('papers', path_to_paper)), port=port)
    # pprint(parsed_pdf)
    with open(os.path.join('parsed_papers', path_to_paper.replace('.pdf', '.json')), 'w', encoding='utf-8') as file:
        json.dump(parsed_pdf, file, indent=4)
