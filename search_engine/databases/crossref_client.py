import json
import logging
import os
import threading
import time
from datetime import datetime
from pprint import pprint
from typing import Iterator

import requests

from search_engine.databases.database_client import DatabaseClient, SearchResult, SupportedSources, SearchStatus
from utils.requests_manager import RequestsManager


class CrossrefClient(DatabaseClient):
    MAX_LIMIT = 1000

    def __init__(self):
        self._api_endpoint = 'https://api.crossref.org/works'
        self._requests_manager = RequestsManager()

        super().__init__(SupportedSources.CROSSREF)

    def search_publications(self, query: str, limit: int = 100, search_id: str = '') -> Iterator[SearchResult]:
        with threading.Lock():
            self._searches[search_id] = {
                'status': SearchStatus.WORKING,
                'documents_to_pull': limit,
                'kill_signal_occurred': False
            }
        responses = self.__query_api(query.strip(), limit=limit, search_id=search_id)
        results = []

        for response in responses:
            results += response.get('message', {}).get('items', [])

        if not results:
            return

        for n, result in enumerate(results):
            yield SearchResult(raw_data=dict(result), source=SupportedSources.CROSSREF)

            if n + 1 == limit:
                break

    def __query_api(self, query: str, limit: int, search_id: str = '') -> list:
        responses = []
        total_results = 0

        while limit > 0:
            limit_ = min(limit, CrossrefClient.MAX_LIMIT)
            response = self._requests_manager.get(
                f'{self._api_endpoint}',
                params={
                    'query': query,
                    'rows': limit_,
                    'offset': total_results
                },
                max_failures=10
            )

            if not isinstance(response, requests.Response):
                return responses

            if response.status_code == 200:
                result_json = response.json()
                result_size = len(result_json.get('message', {}).get('items', []))

                if result_size == 0:
                    break

                responses.append(result_json)
                total_results += result_size
                limit -= result_size

                if limit <= 0:
                    with threading.Lock():
                        self._searches[search_id]['status'] = SearchStatus.WAITING
                        self._searches[search_id]['documents_to_pull'] -= total_results
            else:
                # print(f'Error code {response.status_code}, {response.content}')
                with threading.Lock():
                    if total_results < limit:
                        self._searches[search_id]['status'] = SearchStatus.FINISHED_OUT_OF_DOCUMENTS
                    else:
                        self._searches[search_id]['status'] = SearchStatus.FINISHED_WITH_ERROR
                    self._searches[search_id]['documents_to_pull'] -= total_results

                logging.error(f'Error code {response.status_code}, {response.content}')
                return responses

            # print(f'\rcrossref: {total_results}', end='')
            logging.info(f'crossref: {total_results}')
            time.sleep(1)

        # print(f'\nTotal documents found on Crossref: {total_results}')
        return responses
