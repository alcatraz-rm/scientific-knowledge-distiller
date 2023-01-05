import time
from pprint import pprint
from typing import Iterator

import requests

from search_engine.databases.database import DatabaseClient, SearchResult, SupportedSources


class InternetArchiveClient(DatabaseClient):
    MAX_LIMIT = 500

    def __init__(self):
        self._headers = {'accept': 'application/json'}
        self._api_endpoint = 'https://scholar.archive.org/search'
        super().__init__()

    def search_publications(self, query: str, limit: int = 100) -> Iterator[SearchResult]:
        responses = self.__query_api(query, limit)

        for response in responses:
            for raw_pub in response.get('results'):
                yield SearchResult(raw_pub, source=SupportedSources.INTERNET_ARCHIVE)

    def __query_api(self, query: str, limit: int = 100):
        print('----------------------------')
        print(f'Start Internet Archive search: {query}')

        responses = []
        offset = 0

        while limit:
            limit_ = min(InternetArchiveClient.MAX_LIMIT, limit)
            query_params = {'q': query, 'limit': limit_, 'offset': offset}

            response = requests.get(self._api_endpoint, params=query_params, headers=self._headers)
            if response.status_code == 200:
                responses.append(response.json())
            else:
                print(f'Error code {response.status_code}, {response.content}')
                return responses

            limit -= limit_
            offset += limit_
            time.sleep(2)
            print(f'\rinternet archive: {offset}', end='')

        print(f'\nTotal documents found on Internet Archive: {offset}')
        return responses




