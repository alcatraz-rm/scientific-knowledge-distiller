import json
import logging
import os
import threading
import time
from datetime import datetime
from pprint import pprint
from typing import Iterator
from uuid import UUID

import requests

from search_engine.databases.database_client import DatabaseClient, SearchResult, SupportedSources, SearchStatus
from utils.requests_manager import RequestsManager


class CoreClient(DatabaseClient):
    MAX_LIMIT = 200

    def __init__(self):
        self.__api_key = os.getenv('CORE_API_KEY')
        self._api_endpoint = 'https://api.core.ac.uk/v3/'
        self._requests_manager = RequestsManager()

        super().__init__(SupportedSources.CORE)

    def search_publications(self, query: str, search_id: UUID, limit: int = 100) -> Iterator[SearchResult]:
        self._create_search(search_id, limit)
        responses = self.__query_api(query.strip(), search_id=search_id)
        results = []

        for response in responses:
            results += response.get('results')

        if not results:
            return

        documents_pulled = self._documents_pulled(search_id)

        for n, result in enumerate(results):
            yield SearchResult(raw_data=dict(result), source=SupportedSources.CORE)

            if n + 1 == documents_pulled:
                break

    def __query_api(self, query: str, search_id: UUID = '') -> list:
        responses = []
        headers = {'Authorization': f'Bearer {self.__api_key}'}
        total_results = 0
        failures_number = 0

        max_limit = CoreClient.MAX_LIMIT

        scroll_id = None
        counter = 0
        while self.documents_to_pull(search_id) > 0:
            query_data = {'q': query, 'limit': min(max_limit, self.documents_to_pull(search_id) - counter)}

            if not scroll_id:
                query_data['scroll'] = True
            else:
                query_data['scrollId'] = scroll_id

            response = self._requests_manager.post(f'{self._api_endpoint}search/works', data=json.dumps(query_data),
                                                   headers=headers, max_failures=0)

            if not isinstance(response, requests.Response):
                self.change_limit(search_id, -counter)
                counter = 0
                self._change_status(SearchStatus.FINISHED, search_id)
                break

            if response.status_code == 200:
                result_json = response.json()
                result_size = len(result_json.get('results', []))

                if result_size == 0:
                    self.change_limit(search_id, -counter)
                    counter = 0
                    self._change_status(SearchStatus.FINISHED, search_id)
                    break

                responses.append(result_json)
                total_results += result_size
                counter += result_size
                scroll_id = result_json['scrollId']

                if counter >= self.documents_to_pull(search_id):
                    self.change_limit(search_id, -counter)
                    counter = 0
                    self._change_status(SearchStatus.WAITING, search_id)

                    kill = False

                    while True:
                        if self._kill_signal_occurred(search_id):
                            kill = True
                            break
                        if self.documents_to_pull(search_id) > 0:
                            break

                        time.sleep(5)

                    if kill:
                        break

            elif response.status_code == 429:
                retry_after = response.headers.get('X-RateLimit-Retry-After', '')
                sleep_time = 60
                if retry_after:
                    retry_after = datetime.fromisoformat(retry_after.replace('+0000', '')).replace(tzinfo=datetime.utcnow().tzinfo)
                    sleep_time = (retry_after - datetime.utcnow()).seconds + 10  # 10 seconds just in case
                logging.error(f'Too many requests on Core, waiting {sleep_time} secs...')
                time.sleep(sleep_time)
            elif response.status_code == 500 and 'Error: Allowed memory size' in response.text:
                if max_limit > 20:
                    logging.error(
                        f"Can't fetch results with max limit of {max_limit}, setting max limit to {max_limit // 2}")
                    max_limit //= 2
                else:
                    self.change_limit(search_id, -counter)
                    counter = 0
                    self._change_status(SearchStatus.FINISHED, search_id)
                    break
            else:
                logging.error(f'Error code {response.status_code}, {response.content}')

                if failures_number < 5:
                    failures_number += 1
                    time.sleep(10)
                    continue

                self.change_limit(search_id, -counter)
                counter = 0
                self._change_status(SearchStatus.FINISHED, search_id)
                break

            logging.info(f'core: {total_results}')

        self._terminate(search_id)
        return responses

    def _create_search(self, search_id: UUID, limit: int):
        super(CoreClient, self)._create_search(search_id, limit)

    def _change_status(self, status: SearchStatus, search_id: UUID):
        super(CoreClient, self)._change_status(status, search_id)

    def _terminate(self, search_id: UUID):
        super(CoreClient, self)._terminate(search_id)

    def _documents_pulled(self, search_id: UUID) -> int:
        return super(CoreClient, self)._documents_pulled(search_id)

    def _kill_signal_occurred(self, search_id: UUID):
        return super(CoreClient, self)._kill_signal_occurred(search_id)

    # note: don't call this manually
    def send_kill_signal(self, search_id: UUID):
        super(CoreClient, self).send_kill_signal(search_id)

    def documents_to_pull(self, search_id: UUID) -> int:
        return super(CoreClient, self).documents_to_pull(search_id)

    def change_limit(self, search_id: UUID, delta: int):
        super(CoreClient, self).change_limit(search_id, delta)
