import json
import os
from pprint import pprint

import requests

papers_paths = os.listdir('papers')
ids = {}

for path_to_paper in papers_paths:
    ids[path_to_paper] = []

with open('papers_keywords.json', 'w', encoding='utf-8') as file:
    json.dump(ids, file, indent=4)
    # references = requests.post('https://ref.scholarcy.com/api/references/extract',
    #                            params={'document_type': 'full_paper',
    #                                    'resolve_references': True,
    #                                    'engine': 'v1'},
    #                            files={'file': open(os.path.join('papers', path_to_paper), 'rb')}).json()['references']
    # pprint(references)
    # input()
