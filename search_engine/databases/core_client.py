import json
import os
import time
from datetime import datetime
from pprint import pprint
from typing import Iterator

import requests

from search_engine.databases.database_client import DatabaseClient, SearchResult, SupportedSources


class CoreClient(DatabaseClient):
    MAX_LIMIT = 100

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

        for n, result in enumerate(results):
            yield SearchResult(raw_data=dict(result), source=SupportedSources.CORE)

            if n + 1 == limit:
                break

    def __query_api(self, query: str, limit: int) -> list:
        responses = []
        headers = {'Authorization': f'Bearer {self.__api_key}'}
        total_results = 0

        print('----------------------------')
        print(f'Start Core search: {query}')

        scroll_id = None
        while limit > 0:
            query_data = {'q': query, 'limit': CoreClient.MAX_LIMIT}

            if not scroll_id:
                query_data['scroll'] = True
            else:
                query_data['scrollId'] = scroll_id

            response = requests.post(f'{self._api_endpoint}search/works', data=json.dumps(query_data), headers=headers)
            if response.status_code == 200:
                result_json = response.json()
                result_size = len(result_json.get('results', []))

                if result_size == 0:
                    break

                responses.append(result_json)
                total_results += result_size
                scroll_id = result_json['scrollId']
                limit -= result_size
            elif response.status_code == 429:
                retry_after = response.headers.get('X-RateLimit-Retry-After', '')
                sleep_time = 60
                if retry_after:
                    retry_after = datetime.fromisoformat(retry_after).replace(tzinfo=datetime.utcnow().tzinfo)
                    sleep_time = (retry_after - datetime.utcnow()).seconds + 2  # 2 seconds just in case
                print(f'\nToo many requests on Core, waiting {sleep_time} secs...')
                time.sleep(sleep_time)
            else:
                print(f'Error code {response.status_code}, {response.content}')
                return responses

            print(f'\rcore: {total_results}', end='')

        print(f'\nTotal documents found on Core: {total_results}')
        return responses
