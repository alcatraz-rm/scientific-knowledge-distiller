import logging
import os
import threading
import time
from pprint import pprint
from typing import Iterator

import requests

from search_engine.databases.database_client import DatabaseClient, SearchResult, SupportedSources, SearchStatus
from utils.requests_manager import RequestsManager


class UnpaywallClient(DatabaseClient):
    MAX_LIMIT = 50

    def __init__(self):
        self.__auth_email = os.getenv('UNPAYWALL_EMAIL')
        self._api_endpoint = 'https://api.unpaywall.org/'
        self._requests_manager = RequestsManager()

        super().__init__(SupportedSources.UNPAYWALL)

    def search_publications(self, query: str, limit: int = 100, search_id: str = '') -> Iterator[SearchResult]:
        with threading.Lock():
            self._searches[search_id] = {
                'status': SearchStatus.WORKING,
                'documents_to_pull': limit,
                'kill_signal_occurred': False
            }
        responses = self.__query_api(query.strip(), limit, search_id=search_id)

        counter = 0
        for response in responses:
            for pub in response['results']:
                if counter == limit:
                    return

                yield SearchResult(pub['response'], source=SupportedSources.UNPAYWALL)
                counter += 1

    def __query_api(self, query: str, limit: int = 100, search_id: str = '') -> list:
        endpoint = f'{self._api_endpoint}v2/search'
        responses = []

        page = 1
        total_results = 0

        while limit > 0:
            response = self._requests_manager.get(
                endpoint,
                params={
                    'email': self.__auth_email,
                    'query': query,
                    'page': page
                },
                max_failures=10
            )

            if not isinstance(response, requests.Response):
                return responses

            if response.status_code == 200:
                response_json = response.json()
                results_size = len(response_json['results'])

                if results_size == 0:
                    break

                responses.append(response_json)
                total_results += results_size
            else:
                # print(f'Error code {response.status_code}, {response.content}')
                logging.error(f'Error code {response.status_code}, {response.content}')
                return responses

            limit -= results_size
            page += 1
            # print(f'\runpaywall: {total_results}', end='')
            logging.info(f'unpaywall: {total_results}')

            if limit <= 0:
                with threading.Lock():
                    self._searches[search_id]['status'] = SearchStatus.WAITING
                    self._searches[search_id]['documents_to_pull'] -= total_results

            time.sleep(2)

        # print(f'\nTotal documents found on Unpaywall: {total_results}')
        return responses

