import json
import os
from pprint import pprint

import requests

email = 'g.yakimov@g.nsu.ru'
url = 'https://api.unpaywall.org/v2/search'

query = 'blockchain'
params = {'query': query, 'email': email, 'is_oa': True}

response = requests.get(url, params=params).json()
pprint(response)

with open(os.path.join('responses_examples', 'ourresearch_example.json'), 'w', encoding='utf-8') as file:
    json.dump(response, file, indent=4)
