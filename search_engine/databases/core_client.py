import json
import logging
import os
import time
from datetime import datetime
from pprint import pprint
from typing import Iterator

import requests

from search_engine.databases.database_client import DatabaseClient, SearchResult, SupportedSources
from utils.requests_manager import RequestsManager


class CoreClient(DatabaseClient):
    MAX_LIMIT = 200

    def __init__(self):
        self.__api_key = os.getenv('CORE_API_KEY')
        self._api_endpoint = 'https://api.core.ac.uk/v3/'
        self._requests_manager = RequestsManager()

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
        failures_number = 0

        max_limit = CoreClient.MAX_LIMIT

        # print('----------------------------')
        # print(f'Start Core search: {query}')

        scroll_id = None
        while limit > 0:
            query_data = {'q': query, 'limit': min(max_limit, limit)}

            if not scroll_id:
                query_data['scroll'] = True
            else:
                query_data['scrollId'] = scroll_id

            response = self._requests_manager.post(f'{self._api_endpoint}search/works', data=json.dumps(query_data),
                                                   headers=headers, max_failures=0)

            if not isinstance(response, requests.Response):
                return responses

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
                    retry_after = datetime.fromisoformat(retry_after.replace('+0000', '')).replace(tzinfo=datetime.utcnow().tzinfo)
                    sleep_time = (retry_after - datetime.utcnow()).seconds + 2  # 2 seconds just in case
                # print(f'\nToo many requests on Core, waiting {sleep_time} secs...')
                logging.error(f'Too many requests on Core, waiting {sleep_time} secs...')

                time.sleep(sleep_time)
            elif response.status_code == 500 and 'Error: Allowed memory size' in response.text:
                if max_limit > 20:
                    logging.error(
                        f"Can't fetch results with max limit of {max_limit}, setting max limit to {max_limit // 2}")
                    max_limit //= 2
            else:
                # print(f'Error code {response.status_code}, {response.content}')
                logging.error(f'Error code {response.status_code}, {response.content}')

                if failures_number < 20:
                    failures_number += 1
                    time.sleep(10)
                    continue
                return responses

            # print(f'\rcore: {total_results}', end='')
            logging.info(f'core: {total_results}')

        # print(f'\nTotal documents found on Core: {total_results}')
        return responses
