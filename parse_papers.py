import json
import os
from pathlib import Path
from pprint import pprint

to_ignore = ['.DS_Store']
papers_paths = os.listdir('papers')

for file in to_ignore:
    papers_paths.remove(file)

citations = []

with open('papers_data.json', 'r', encoding='utf-8') as file:
    metadata = json.load(file)

for path_to_paper in papers_paths:
    print(path_to_paper)

    parsed_pdf = ''
    pprint(parsed_pdf)
    exit(0)
