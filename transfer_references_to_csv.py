import csv
import json
import os
import ssl
import time
from pprint import pprint

import requests
import urllib3

to_ignore = ['.DS_Store']
papers_paths = os.listdir('papers')

for file in to_ignore:
    papers_paths.remove(file)

citations = []

with open('papers_data.json', 'r', encoding='utf-8') as file:
    metadata = json.load(file)

for path_to_paper in papers_paths:
    print(path_to_paper)
    try:
        references = requests.post('https://ref.scholarcy.com/api/references/extract',
                                   params={'document_type': 'full_paper',
                                           'resolve_references': True,
                                           'engine': 'v1'},
                                   files={'file': open(os.path.join('papers', path_to_paper), 'rb')}).json()[
            'references']
    except (ssl.SSLEOFError, requests.exceptions.SSLError, urllib3.exceptions.MaxRetryError):
        print('ssl error, wait 60 secs')
        time.sleep(60)

        references = requests.post('https://ref.scholarcy.com/api/references/extract',
                                   params={'document_type': 'full_paper',
                                           'resolve_references': True,
                                           'engine': 'v1'},
                                   files={'file': open(os.path.join('papers', path_to_paper), 'rb')}).json()[
            'references']

    for reference in references:
        citations.append(
            {
                'paper_id': path_to_paper,
                'paper_keywords': ','.join(metadata[path_to_paper]['keywords']),
                'paper_title': metadata[path_to_paper]['title'],
                'paper_abstract': metadata[path_to_paper]['abstract'],
                'citation': reference
            }
        )
    time.sleep(60)

with open('citations.csv', 'w', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=citations[0].keys())
    writer.writeheader()
    writer.writerows(citations)
