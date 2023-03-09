import logging
import os
import time
from pprint import pprint
from typing import Iterator

import requests

from search_engine.databases.database_client import DatabaseClient, SearchResult, SupportedSources
from semanticscholar import SemanticScholar

from utils.requests_manager import RequestsManager


class SematicScholarClient(DatabaseClient):
    MAX_LIMIT = 100

    def __init__(self):
        # self._sch = SemanticScholar()
        self._requests_manager = RequestsManager()
        self._api_endpoint = 'https://api.semanticscholar.org/graph/v1/paper/search'
        self._api_key = os.getenv('SEMANTIC_SCHOLAR_API_KEY')
        super().__init__()

    def search_publications(self, query: str, limit: int = 100) -> Iterator[SearchResult]:
        responses = self.__query_api(query.strip(), limit=limit)
        results = []

        for response in responses:
            results += response.get('data', [])

        if not results:
            return

        for n, result in enumerate(results):
            yield SearchResult(raw_data=dict(result), source=SupportedSources.SEMANTIC_SCHOLAR)

            if n + 1 == limit:
                break

    def __query_api(self, query: str, limit: int) -> list:
        responses = []
        total_results = 0

        # print('----------------------------')
        # print(f'Start Semantic Scholar search: {query}')

        while limit > 0:
            limit_ = min(limit, SematicScholarClient.MAX_LIMIT)

            if total_results + limit_ >= 10000:
                limit_ = 9999 - total_results

            response = self._requests_manager.get(
                f'{self._api_endpoint}',
                params={
                    'query': query,
                    'limit': limit_,
                    'offset': total_results,
                    'fields': 'externalIds,url,title,abstract,venue,publicationVenue,year,referenceCount,'
                              'isOpenAccess,openAccessPdf,publicationDate,authors,journal'
                },
                headers={
                    'api-key': self._api_key
                },
                max_failures=10
            )

            if not isinstance(response, requests.Response):
                return responses

            if response.status_code == 200:
                result_json = response.json()

                result_size = len(result_json.get('data', []))

                if result_size == 0:
                    break

                responses.append(result_json)
                total_results += result_size
                limit -= result_size
            elif response.status_code == 429:
                print('Too many requests, waiting 15 secs...')
                time.sleep(15)
            else:
                # print(f'Error code {response.status_code}, {response.content}')
                logging.error(f'Error code {response.status_code}, {response.content}')
                return responses

            # print(f'\rsemantic scholar: {total_results}', end='')
            logging.info(f'semantic scholar: {total_results}')
            time.sleep(1)

        # print(f'\nTotal documents found on SemanticScholar: {total_results}')
        return responses
