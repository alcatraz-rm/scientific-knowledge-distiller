import os
import time
from pprint import pprint
from typing import Iterator

import requests

from search_engine.databases.database import DatabaseClient, SearchResult


class UnpaywallClient(DatabaseClient):
    MAX_LIMIT = 50

    def __init__(self):
        self.__auth_email = os.getenv('UNPAYWALL_EMAIL')
        self._api_endpoint = 'https://api.unpaywall.org/'
        super().__init__()

    def search_publications(self, query: str, limit: int = 100) -> Iterator[SearchResult]:
        responses = self.__query_api(query.strip(), limit)

        counter = 0
        for response in responses:
            for pub in response['results']:
                if counter == limit:
                    return

                yield SearchResult(pub['response'], 'unpaywall')
                counter += 1

    def __query_api(self, query: str, limit: int = 100) -> list:
        endpoint = f'{self._api_endpoint}v2/search'
        responses = []

        print('----------------------------')
        print(f'Start Unpaywall search: {query}')

        page = 1

        while limit:
            limit_ = min(limit, UnpaywallClient.MAX_LIMIT)
            response = requests.get(
                endpoint,
                params={
                    'email': self.__auth_email,
                    'query': query,
                    'page': page
                }
            )

            if response.status_code == 200:
                responses.append(response.json())
            else:
                print(f'Error code {response.status_code}, {response.content}')
                return responses

            limit -= limit_
            page += 1
            print(f'\runpaywall: {(page - 1) * UnpaywallClient.MAX_LIMIT}', end='')

            time.sleep(2)

        print(f'\nTotal documents found on Unpaywall: {(page - 1) * UnpaywallClient.MAX_LIMIT}')
        return responses

