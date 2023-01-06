import os
import time
from pprint import pprint
from typing import Iterator

import requests

from search_engine.databases.database_client import DatabaseClient, SearchResult, SupportedSources


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

                yield SearchResult(pub['response'], source=SupportedSources.UNPAYWALL)
                counter += 1

    def __query_api(self, query: str, limit: int = 100) -> list:
        endpoint = f'{self._api_endpoint}v2/search'
        responses = []

        print('----------------------------')
        print(f'Start Unpaywall search: {query}')

        page = 1
        total_results = 0

        while limit > 0:
            response = requests.get(
                endpoint,
                params={
                    'email': self.__auth_email,
                    'query': query,
                    'page': page
                }
            )

            if response.status_code == 200:
                response_json = response.json()
                results_size = len(response_json['results'])

                if results_size == 0:
                    break

                responses.append(response_json)
                total_results += results_size
            else:
                print(f'Error code {response.status_code}, {response.content}')
                return responses

            limit -= results_size
            page += 1
            print(f'\runpaywall: {total_results}', end='')

            time.sleep(2)

        print(f'\nTotal documents found on Unpaywall: {total_results}')
        return responses

