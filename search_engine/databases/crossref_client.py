import logging
import time
from typing import Iterator
from uuid import UUID

import requests

from search_engine.databases.database_client import DatabaseClient, Document, SupportedSources, SearchStatus
from utils.requests_manager import RequestsManager


class CrossrefClient(DatabaseClient):
    MAX_LIMIT = 1000

    def __init__(self):
        self._api_endpoint = 'https://api.crossref.org/works'
        self._requests_manager = RequestsManager()

        super().__init__(SupportedSources.CROSSREF)

    def search_publications(self, query: str, search_id: UUID, limit: int = 100) -> Iterator[Document]:
        self._create_search(search_id, limit)
        responses = self.__query_api(query.strip(), search_id=search_id)
        results = []

        for response in responses:
            results += response.get('message', {}).get('items', [])

        if not results:
            return

        documents_pulled = self._documents_pulled(search_id)

        for n, result in enumerate(results):
            yield Document(raw_data=dict(result), source=SupportedSources.CROSSREF)

            if n + 1 == documents_pulled:
                break

    def __query_api(self, query: str, search_id: UUID = '') -> list:
        responses = []
        total_results = 0
        counter = 0

        while self.documents_to_pull(search_id) > 0:
            limit_ = min(CrossrefClient.MAX_LIMIT, self.documents_to_pull(search_id) - counter)
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
                self.change_limit(search_id, -counter)
                counter = 0
                self._change_status(SearchStatus.FINISHED, search_id)
                break

            if response.status_code == 200:
                result_json = response.json()
                result_size = len(result_json.get('message', {}).get('items', []))

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
            else:
                self.change_limit(search_id, -counter)
                counter = 0
                self._change_status(SearchStatus.FINISHED, search_id)

                logging.error(f'Error code {response.status_code}, {response.content}')
                break

            logging.info(f'crossref: {total_results}')
            time.sleep(1)

        self._terminate(search_id)
        return responses

    def _create_search(self, search_id: UUID, limit: int):
        super(CrossrefClient, self)._create_search(search_id, limit)

    def _change_status(self, status: SearchStatus, search_id: UUID):
        super(CrossrefClient, self)._change_status(status, search_id)

    def _terminate(self, search_id: UUID):
        super(CrossrefClient, self)._terminate(search_id)

    def _documents_pulled(self, search_id: UUID) -> int:
        return super(CrossrefClient, self)._documents_pulled(search_id)

    def _kill_signal_occurred(self, search_id: UUID):
        return super(CrossrefClient, self)._kill_signal_occurred(search_id)

    # note: don't call this manually
    def send_kill_signal(self, search_id: UUID):
        super(CrossrefClient, self).send_kill_signal(search_id)

    def documents_to_pull(self, search_id: UUID) -> int:
        return super(CrossrefClient, self).documents_to_pull(search_id)

    def change_limit(self, search_id: UUID, delta: int):
        super(CrossrefClient, self).change_limit(search_id, delta)
