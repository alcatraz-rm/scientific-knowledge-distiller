import logging
import time
from typing import Iterator
from uuid import UUID

import requests

from search_engine.databases.database_client import DatabaseClient, Document, SupportedSources, SearchStatus
from utils.requests_manager import RequestsManager


class PapersWithCodeClient(DatabaseClient):
    MAX_LIMIT = 500

    def __init__(self):
        self._api_endpoint = 'https://paperswithcode.com/api/v1/search/'
        self._requests_manager = RequestsManager()

        super().__init__(SupportedSources.PAPERS_WITH_CODE)

    def search_publications(self, query: str, search_id: UUID, limit: int = 100) -> Iterator[Document]:
        self._create_search(search_id, limit)
        responses = self.__query_api(query.strip(), search_id)

        counter = 0
        documents_pulled = self._documents_pulled(search_id)

        for response in responses:
            for pub in response['results']:
                yield Document(pub, source=SupportedSources.PAPERS_WITH_CODE)
                counter += 1

                if counter == documents_pulled:
                    return

    def __query_api(self, query: str, search_id: UUID = '') -> list:
        responses = []

        page = 1
        total_results = 0
        counter = 0

        while self.documents_to_pull(search_id) > 0:
            request_limit = min(self.documents_to_pull(search_id) - counter, PapersWithCodeClient.MAX_LIMIT)
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
                self.change_limit(search_id, -counter)
                counter = 0
                self._change_status(SearchStatus.FINISHED, search_id)
                break

            if response.status_code == 200:
                response_json = response.json()
                results_size = len(response_json['results'])

                if results_size == 0:
                    self.change_limit(search_id, -counter)
                    counter = 0
                    self._change_status(SearchStatus.FINISHED, search_id)
                    break

                responses.append(response_json)
                total_results += results_size
                counter += results_size

                if results_size < request_limit:
                    self.change_limit(search_id, -counter)
                    counter = 0
                    self._change_status(SearchStatus.FINISHED, search_id)
                    break
            else:
                logging.error(f'Error code {response.status_code}, {response.content}')
                self.change_limit(search_id, -counter)
                counter = 0
                self._change_status(SearchStatus.FINISHED, search_id)
                break

            page += 1
            logging.info(f'papers_with_code: {total_results}')

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

            time.sleep(2)

        self._terminate(search_id)
        return responses

    def _create_search(self, search_id: UUID, limit: int):
        super(PapersWithCodeClient, self)._create_search(search_id, limit)

    def _change_status(self, status: SearchStatus, search_id: UUID):
        super(PapersWithCodeClient, self)._change_status(status, search_id)

    def _terminate(self, search_id: UUID):
        super(PapersWithCodeClient, self)._terminate(search_id)

    def _documents_pulled(self, search_id: UUID) -> int:
        return super(PapersWithCodeClient, self)._documents_pulled(search_id)

    def _kill_signal_occurred(self, search_id: UUID):
        return super(PapersWithCodeClient, self)._kill_signal_occurred(search_id)

    # note: don't call this manually
    def send_kill_signal(self, search_id: UUID):
        super(PapersWithCodeClient, self).send_kill_signal(search_id)

    def documents_to_pull(self, search_id: UUID) -> int:
        return super(PapersWithCodeClient, self).documents_to_pull(search_id)

    def change_limit(self, search_id: UUID, delta: int):
        super(PapersWithCodeClient, self).change_limit(search_id, delta)
