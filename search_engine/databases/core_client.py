import json
import os
import time
from pprint import pprint
from typing import Iterator

import requests

from search_engine.databases.database import DatabaseClient, SearchResult


class CoreClient(DatabaseClient):
    MAX_LIMIT = 500

    def __init__(self):
        self.__api_key = os.getenv('CORE_API_KEY')
        self._api_endpoint = 'https://api.core.ac.uk/v3/'

        super().__init__()

    def search_publications(self, query: str, limit: int = 100) -> Iterator[SearchResult]:
        responses = self.__query_api(query.strip(), limit=limit)
        results = []

        for response in responses:
            results += response.get('results')

        if not results:
            return

        # pprint(results)
        # pprint(results[0])

        for result in results:
            yield SearchResult(raw_data=dict(result), source='core')

    def __query_api(self, query: str, limit: int) -> list:
        responses = []
        headers = {'Authorization': f'Bearer {self.__api_key}'}
        offset = 0

        while limit:
            limit_ = min(CoreClient.MAX_LIMIT, limit)
            query_data = {'q': query, 'limit': limit_, 'offset': offset}

            response = requests.post(f'{self._api_endpoint}search/works', data=json.dumps(query_data), headers=headers)
            if response.status_code == 200:
                responses.append(response.json())
            else:
                print(f'Error code {response.status_code}, {response.content}')

            limit -= limit_
            offset += limit_
            time.sleep(2)
            print(offset)

        return responses
