import json
import os
from pprint import pprint
from typing import Iterator

import requests

from search_engine.databases.database import DatabaseClient, SearchResult


class CoreClient(DatabaseClient):
    def __init__(self):
        self.__api_key = os.getenv('CORE_API_KEY')
        self._api_endpoint = 'https://api.core.ac.uk/v3/'

        super().__init__()

    def search_publications(self, query: str, limit: int = 100) -> Iterator[SearchResult]:
        results = self.__query_api(query, limit=limit)['results']

        # pprint(results)
        print(len(results))

        for result in results:
            yield SearchResult(raw_data=dict(result), source='core')

    def __query_api(self, query, limit):
        headers = {'Authorization': f'Bearer {self.__api_key}'}
        query = {'q': query, 'limit': limit}
        response = requests.post(f'{self._api_endpoint}search/works', data=json.dumps(query), headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f'Error code {response.status_code}, {response.content}')
