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


class OpenAlexClient(DatabaseClient):
    MAX_LIMIT = 200

    def __init__(self):
        self._api_endpoint = 'https://api.openalex.org/works'
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
            yield SearchResult(raw_data=dict(result), source=SupportedSources.OPENALEX)

            if n + 1 == limit:
                break

    def __query_api(self, query: str, limit: int) -> list:
        responses = []
        total_results = 0
        failures_number = 0

        max_limit = OpenAlexClient.MAX_LIMIT
        cursor = '*'
        while limit > 0:
            query_data = {'search': query, 'per-page': min(max_limit, limit), 'cursor': cursor}
            response = self._requests_manager.get(self._api_endpoint, params=query_data, max_failures=10)

            if not isinstance(response, requests.Response):
                return responses

            if response.status_code == 200:
                result_json = response.json()
                result_size = len(result_json.get('results', []))

                if result_size == 0:
                    break

                responses.append(result_json)
                total_results += result_size
                cursor = result_json['meta'].get('next_cursor')
                limit -= result_size

                if not cursor:
                    break
            else:
                # print(f'Error code {response.status_code}, {response.content}')
                logging.error(f'Error code {response.status_code}, {response.content}')

                if failures_number < 20:
                    failures_number += 1
                    time.sleep(10)
                    continue
                return responses

            logging.info(f'openalex: {total_results}')

        return responses
