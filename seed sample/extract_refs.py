import json
import os
from pathlib import Path
from science_parse_api.api import parse_pdf

to_ignore = ['.DS_Store']
papers_paths = os.listdir(os.path.join('sample_2', 'seed_docs'))

host = 'http://127.0.0.1'
port = '8080'

for file in to_ignore:
    if file in papers_paths:
        papers_paths.remove(file)

for path_to_paper in papers_paths:
    print(path_to_paper)

    parsed_pdf = parse_pdf(host, Path(os.path.join('sample_2', 'seed_docs', 'references', path_to_paper)), port=port)
    with open(os.path.join(path_to_paper.replace('.pdf', '.json')), 'w', encoding='utf-8') as file:
        json.dump(parsed_pdf, file, indent=4)
