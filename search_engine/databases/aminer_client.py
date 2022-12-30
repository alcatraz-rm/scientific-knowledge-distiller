import os
import time
from pprint import pprint
from typing import Iterator

import requests

from search_engine.databases.database import DatabaseClient, SearchResult


class AminerClient(DatabaseClient):
    MAX_LIMIT = 99

    def __init__(self):
        self._api_endpoint = 'https://api.aminer.org/api/search/pub/advanced'
        super().__init__()

    def search_publications(self, query: str, limit: int = 100) -> Iterator[SearchResult]:
        responses = self.__query_api(query.strip(), limit)

        for response in responses:
            for pub in response['results']:
                yield SearchResult(pub['response'], 'unpaywall')

    def __query_api(self, query: str, limit: int = 100) -> list:
        responses = []

        print('----------------------------')
        print(f'Start AMiner search: {query}')

        pubs_found = 0
        pubs_found_last_request = 0

        while limit:
            response = requests.get(
                self._api_endpoint,
                params={
                    'term': query,
                    'offset': pubs_found,
                    'size': min(AminerClient.MAX_LIMIT, limit)
                }
            )

            if response.status_code == 200:
                result = response.json()
                responses.append(result)
                pubs_found_last_request = len(result['result'])
            else:
                print(f'Error code {response.status_code}, {response.content}')
                return responses

            limit -= pubs_found_last_request
            pubs_found += pubs_found_last_request
            print(f'\raminer: {pubs_found}', end='')

            if pubs_found >= limit:
                break

            time.sleep(2)

        print(f'\nTotal documents found on AMiner: {pubs_found}')
        return responses
