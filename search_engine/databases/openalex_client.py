import logging
import time
from typing import Iterator
from uuid import UUID

import requests

from search_engine.databases.database_client import DatabaseClient, Document, SupportedSources, SearchStatus
from utils.requests_manager import RequestsManager


class OpenAlexClient(DatabaseClient):
    MAX_LIMIT = 200

    def __init__(self):
        self._api_endpoint = 'https://api.openalex.org/works'
        self._requests_manager = RequestsManager()

        super().__init__(SupportedSources.OPENALEX)

    def search_publications(self, query: str, search_id: UUID, limit: int = 100) -> Iterator[Document]:
        self._create_search(search_id, limit)
        responses = self.__query_api(query.strip(), search_id=search_id)
        results = []

        for response in responses:
            results += response.get('results')

        return [Document(raw_data=dict(result), source=SupportedSources.OPENALEX) for result in results]

    def __query_api(self, query: str, search_id: UUID = '') -> list:
        responses = []
        total_results = 0
        counter = 0
        failures_number = 0

        max_limit = OpenAlexClient.MAX_LIMIT
        cursor = '*'
        while self.documents_to_pull(search_id) > 0:
            query_data = {'search': query, 'per-page': min(max_limit, self.documents_to_pull(search_id) - counter),
                          'cursor': cursor}
            response = self._requests_manager.get(
                self._api_endpoint, params=query_data, max_failures=10)

            if not isinstance(response, requests.Response):
                self.change_limit(search_id, -counter)
                self._change_status(SearchStatus.FINISHED, search_id)
                break

            if response.status_code == 200:
                result_json = response.json()
                result_size = len(result_json.get('results', []))

                if result_size == 0:
                    self.change_limit(search_id, -counter)
                    self._change_status(SearchStatus.FINISHED, search_id)
                    break

                responses.append(result_json)
                total_results += result_size
                counter += result_size
                cursor = result_json['meta'].get('next_cursor')

                if counter >= self.documents_to_pull(search_id):
                    self.change_limit(search_id, -counter)
                    self._change_status(SearchStatus.WAITING, search_id)
                    logging.info(
                        f'Pulled {counter} docs from {self.name}.'
                        f'Total docs pulled: {self._documents_pulled(search_id)}'
                    )
                    counter = 0
                    kill = self._wait(search_id)
                    if kill:
                        logging.info(f'Kill signal for {self.name} occurred.')
                        break

                if not cursor:
                    self.change_limit(search_id, -counter)
                    self._change_status(SearchStatus.FINISHED, search_id)
                    break
            else:
                logging.error(
                    f'Error code {response.status_code}, {response.content}')

                if failures_number < 20:
                    failures_number += 1
                    time.sleep(10)
                    continue

                self.change_limit(search_id, -counter)
                self._change_status(SearchStatus.FINISHED, search_id)
                break

            logging.debug(f'openalex: {total_results}')

        logging.info(
            f'Terminating {self.name} client. Docs pulled: {self._documents_pulled(search_id)}. Docs left: {self.documents_to_pull(search_id)}')
        self._terminate(search_id)
        return responses

    def _create_search(self, search_id: UUID, limit: int):
        super(OpenAlexClient, self)._create_search(search_id, limit)

    def _change_status(self, status: SearchStatus, search_id: UUID):
        super(OpenAlexClient, self)._change_status(status, search_id)

    def _terminate(self, search_id: UUID):
        super(OpenAlexClient, self)._terminate(search_id)

    def _documents_pulled(self, search_id: UUID) -> int:
        return super(OpenAlexClient, self)._documents_pulled(search_id)

    def _kill_signal_occurred(self, search_id: UUID):
        return super(OpenAlexClient, self)._kill_signal_occurred(search_id)

    def _wait(self, search_id: UUID):
        return super(OpenAlexClient, self)._wait(search_id)

    # note: don't call this manually
    def send_kill_signal(self, search_id: UUID):
        super(OpenAlexClient, self).send_kill_signal(search_id)

    def documents_to_pull(self, search_id: UUID) -> int:
        return super(OpenAlexClient, self).documents_to_pull(search_id)

    def change_limit(self, search_id: UUID, delta: int):
        super(OpenAlexClient, self).change_limit(search_id, delta)
