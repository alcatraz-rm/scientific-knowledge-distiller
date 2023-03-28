import json
import logging
import os
import time
from datetime import datetime
from typing import Iterator

import requests

from search_engine.databases.database_client import DatabaseClient, Document, SupportedSources
from utils.requests_manager import RequestsManager

# TODO
class DBLPClient(DatabaseClient):
    MAX_LIMIT = 1000

    def __init__(self):
        self._api_endpoint = 'https://dblp.org/search/publ/api'
        self._requests_manager = RequestsManager()

        super().__init__()

    def search_publications(self, query: str, search_id: UUID, limit: int = 100 = '') -> Iterator[Document]:
        responses = self.__query_api(query.strip(), limit=limit)
        results = []

        for response in responses:
            results += response.get('results')

        if not results:
            return

        for n, result in enumerate(results):
            yield Document(raw_data=dict(result), source=SupportedSources.DBLP)

            if n + 1 == limit:
                break

    def __query_api(self, query: str, limit: int = 100) -> list:
        responses = []

        total_results = 0

        while limit > 0:
            response = self._requests_manager.get(
                self._api_endpoint,
                params={
                    'q': query,
                    'format': 'json',
                    'f': total_results,
                    'h': min(limit, DBLPClient.MAX_LIMIT),
                    'c': 1000
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
                logging.error(f'Error code {response.status_code}, {response.content}')
                return responses

            limit -= results_size
            logging.info(f'dblp: {total_results}')

            time.sleep(2)
        return responses
