# code from example: https://github.com/oacore/apiv3-webinar/blob/main/webinar.ipynb
import json
import os.path
from pprint import pprint

import requests

CORE_API_KEY = 'a3n5ecqI2wO9uQYWzJxKhLToMgZiSjNV'
url = 'https://api.core.ac.uk/v3/'


def get_entity(url_fragment):
    headers = {"Authorization": "Bearer " + CORE_API_KEY}
    response = requests.get(url + url_fragment, headers=headers)
    if response.status_code == 200:
        return response.json(), response.elapsed.total_seconds()
    else:
        print(f"Error code {response.status_code}, {response.content}")


def query_api(url_fragment, query, limit=100):
    headers = {"Authorization": "Bearer " + CORE_API_KEY}
    query = {"q": query, "limit": limit}
    response = requests.post(f"{url}{url_fragment}", data=json.dumps(query), headers=headers)
    if response.status_code == 200:
        return response.json(), response.elapsed.total_seconds()
    else:
        print(f"Error code {response.status_code}, {response.content}")


data_provider, elapsed = get_entity("data-providers/1")
pprint(data_provider)

query = f"blockchain"
results, elapsed = query_api("search/works", query, limit=1)

with open(os.path.join('responses_examples', 'core_example.json'), 'w', encoding='utf-8') as file:
    json.dump(results, file, indent=4)
