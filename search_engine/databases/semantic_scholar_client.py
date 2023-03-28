import logging
import os
import time
from typing import Iterator
from uuid import UUID

import requests

from search_engine.databases.database_client import DatabaseClient, Document, SupportedSources, SearchStatus
from utils.requests_manager import RequestsManager


class SematicScholarClient(DatabaseClient):
    MAX_LIMIT = 100

    def __init__(self):
        # self._sch = SemanticScholar()
        self._requests_manager = RequestsManager()
        self._api_endpoint = 'https://api.semanticscholar.org/graph/v1/paper/search'
        self._api_key = os.getenv('SEMANTIC_SCHOLAR_API_KEY')
        super().__init__(SupportedSources.SEMANTIC_SCHOLAR)

    def search_publications(self, query: str, search_id: UUID, limit: int = 100) -> Iterator[Document]:
        self._create_search(search_id, limit)
        responses = self.__query_api(query.strip(), search_id=search_id)
        results = []

        for response in responses:
            results += response.get('data', [])

        if not results:
            return

        documents_pulled = self._documents_pulled(search_id)

        for n, result in enumerate(results):
            yield Document(raw_data=dict(result), source=SupportedSources.SEMANTIC_SCHOLAR)

            if n + 1 == documents_pulled:
                break

    def __query_api(self, query: str, search_id: UUID = '') -> list:
        responses = []
        total_results = 0
        counter = 0

        while self.documents_to_pull(search_id) > 0:
            limit_ = min(self.documents_to_pull(search_id) - counter, SematicScholarClient.MAX_LIMIT)

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
                self.change_limit(search_id, -counter)
                counter = 0
                self._change_status(SearchStatus.FINISHED, search_id)
                break

            if response.status_code == 200:
                result_json = response.json()
                result_size = len(result_json.get('data', []))

                if result_size == 0:
                    self.change_limit(search_id, -counter)
                    counter = 0
                    self._change_status(SearchStatus.FINISHED, search_id)
                    break

                responses.append(result_json)
                total_results += result_size
                counter += result_size

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
                print('Too many requests, waiting 15 secs...')
                time.sleep(15)
            else:
                logging.error(f'Error code {response.status_code}, {response.content}')
                self.change_limit(search_id, -counter)
                counter = 0
                self._change_status(SearchStatus.FINISHED, search_id)
                break

            logging.info(f'semantic scholar: {total_results}')
            time.sleep(1)

        self._terminate(search_id)
        return responses

    def _create_search(self, search_id: UUID, limit: int):
        super(SematicScholarClient, self)._create_search(search_id, limit)

    def _change_status(self, status: SearchStatus, search_id: UUID):
        super(SematicScholarClient, self)._change_status(status, search_id)

    def _terminate(self, search_id: UUID):
        super(SematicScholarClient, self)._terminate(search_id)

    def _documents_pulled(self, search_id: UUID) -> int:
        return super(SematicScholarClient, self)._documents_pulled(search_id)

    def _kill_signal_occurred(self, search_id: UUID):
        return super(SematicScholarClient, self)._kill_signal_occurred(search_id)

    # note: don't call this manually
    def send_kill_signal(self, search_id: UUID):
        super(SematicScholarClient, self).send_kill_signal(search_id)

    def documents_to_pull(self, search_id: UUID) -> int:
        return super(SematicScholarClient, self).documents_to_pull(search_id)

    def change_limit(self, search_id: UUID, delta: int):
        super(SematicScholarClient, self).change_limit(search_id, delta)
