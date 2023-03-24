import logging
import threading
import time
from pprint import pprint
from typing import Iterator

import requests

from search_engine.databases.database_client import DatabaseClient, SearchResult, SupportedSources, SearchStatus
from utils.requests_manager import RequestsManager


class InternetArchiveClient(DatabaseClient):
    MAX_LIMIT = 500

    def __init__(self):
        self._headers = {'accept': 'application/json'}
        self._api_endpoint = 'https://scholar.archive.org/search'
        self._requests_manager = RequestsManager()

        super().__init__(SupportedSources.INTERNET_ARCHIVE)

    def search_publications(self, query: str, limit: int = 100, search_id: str = '') -> Iterator[SearchResult]:
        with threading.Lock():
            self._searches[search_id] = {
                'status': SearchStatus.WORKING,
                'documents_to_pull': limit,
                'kill_signal_occurred': False
            }
        responses = self.__query_api(query, limit, search_id=search_id)

        for response in responses:
            for raw_pub in response.get('results'):
                yield SearchResult(raw_pub, source=SupportedSources.INTERNET_ARCHIVE)

    def __query_api(self, query: str, limit: int = 100, search_id: str = ''):
        # print('----------------------------')
        # print(f'Start Internet Archive search: {query}')

        responses = []
        offset = 0

        while limit > 0:
            limit_ = min(InternetArchiveClient.MAX_LIMIT, limit)
            query_params = {'q': query, 'limit': limit_, 'offset': offset}

            response = self._requests_manager.get(self._api_endpoint, params=query_params, headers=self._headers,
                                                  max_failures=10)

            if not response:
                return []

            if response.status_code == 200:
                response_json = response.json()
                results_size = len(response_json.get('results', []))
                if results_size == 0:
                    break

                responses.append(response_json)
                limit -= results_size
                offset += results_size

                if limit <= 0:
                    with threading.Lock():
                        self._searches[search_id]['status'] = SearchStatus.WAITING
                        self._searches[search_id]['documents_to_pull'] -= offset
            else:
                # print(f'Error code {response.status_code}, {response.content}')
                logging.error(f'Error code {response.status_code}, {response.content}')
                return responses

            time.sleep(2)
            logging.info(f'internet archive: {offset}')
            # print(f'\rinternet archive: {offset}', end='')

        # print(f'\nTotal documents found on Internet Archive: {offset}')
        return responses
