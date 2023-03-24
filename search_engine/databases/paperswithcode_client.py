import logging
import os
import time
from pprint import pprint
from typing import Iterator

import requests

from search_engine.databases.database_client import DatabaseClient, SearchResult, SupportedSources
from utils.requests_manager import RequestsManager


class PapersWithCodeClient(DatabaseClient):
    MAX_LIMIT = 500

    def __init__(self):
        self._api_endpoint = 'https://paperswithcode.com/api/v1/search/'
        self._requests_manager = RequestsManager()

        super().__init__()

    def search_publications(self, query: str, limit: int = 100) -> Iterator[SearchResult]:
        responses = self.__query_api(query.strip(), limit)

        counter = 0
        for response in responses:
            for pub in response['results']:
                if counter == limit:
                    return

                yield SearchResult(pub, source=SupportedSources.PAPERS_WITH_CODE)
                counter += 1

    def __query_api(self, query: str, limit: int = 100) -> list:
        responses = []

        page = 1
        total_results = 0

        while limit > 0:
            request_limit = min(limit, PapersWithCodeClient.MAX_LIMIT)
            response = self._requests_manager.get(
                self._api_endpoint,
                headers={'accept': 'application/json'},
                params={
                    'q': query,
                    'page': page,
                    'items_per_page': request_limit
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

                if results_size < request_limit:
                    break
            else:
                logging.error(f'Error code {response.status_code}, {response.content}')
                return responses

            limit -= results_size
            page += 1
            logging.info(f'papers_with_code: {total_results}')

            time.sleep(2)

        return responses

