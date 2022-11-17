import json
import os
from pprint import pprint

import arxiv

response = list(arxiv.Search(
  query="blockchain",
  max_results=1
).results())[0]

response_d = response.__dict__
response_d['published'] = str(response_d['published'])
response_d['updated'] = str(response_d['updated'])
response_d['_raw']['published_parsed'] = str(response_d['_raw']['published_parsed'])

with open(os.path.join('responses_examples', 'arxiv_example.txt'), 'w', encoding='utf-8') as file:
    pprint(response_d, stream=file)
