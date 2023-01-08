import json
import os
import time
from datetime import datetime
from pprint import pprint
from typing import Iterator

import requests

from search_engine.databases.database_client import DatabaseClient, SearchResult, SupportedSources


class CrossrefClient(DatabaseClient):
    MAX_LIMIT = 1000

    def __init__(self):
        self._api_endpoint = 'https://api.crossref.org/works'

        super().__init__()

    def search_publications(self, query: str, limit: int = 100) -> Iterator[SearchResult]:
        responses = self.__query_api(query.strip(), limit=limit)
        results = []

        for response in responses:
            results += response.get('message', {}).get('items', [])

        if not results:
            return

        for n, result in enumerate(results):
            yield SearchResult(raw_data=dict(result), source=SupportedSources.CROSSREF)

            if n + 1 == limit:
                break

    def __query_api(self, query: str, limit: int) -> list:
        responses = []
        total_results = 0

        print('----------------------------')
        print(f'Start Crossref search: {query}')

        while limit > 0:
            limit_ = min(limit, CrossrefClient.MAX_LIMIT)
            response = requests.get(
                f'{self._api_endpoint}',
                params={
                    'query': query,
                    'rows': limit_,
                    'offset': total_results
                }
            )

            if response.status_code == 200:
                result_json = response.json()

                result_size = len(result_json.get('message', {}).get('items', []))

                if result_size == 0:
                    break

                responses.append(result_json)
                total_results += result_size
                limit -= result_size
            else:
                print(f'Error code {response.status_code}, {response.content}')
                return responses

            print(f'\rcrossref: {total_results}', end='')
            time.sleep(1)

        print(f'\nTotal documents found on Crossref: {total_results}')
        return responses
