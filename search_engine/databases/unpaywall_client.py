import logging
import os
import time
from typing import Iterator
from uuid import UUID

import requests

from search_engine.databases.database_client import DatabaseClient, Document, SupportedSources, SearchStatus
from utils.requests_manager import RequestsManager


class UnpaywallClient(DatabaseClient):
    MAX_LIMIT = 50

    def __init__(self):
        self.__auth_email = os.getenv('UNPAYWALL_EMAIL')
        self._api_endpoint = 'https://api.unpaywall.org/'
        self._requests_manager = RequestsManager()

        super().__init__(SupportedSources.UNPAYWALL)

    def search_publications(self, query: str, search_id: UUID, limit: int = 100) -> Iterator[Document]:
        self._create_search(search_id, limit)
        responses = self.__query_api(query.strip(), search_id=search_id)

        documents_pulled = self._documents_pulled(search_id)

        counter = 0
        for response in responses:
            for pub in response['results']:
                yield Document(pub['response'], source=SupportedSources.UNPAYWALL)
                counter += 1

                if counter == documents_pulled:
                    return

    def __query_api(self, query: str, search_id: UUID = '') -> list:
        endpoint = f'{self._api_endpoint}v2/search'
        responses = []

        page = 1
        total_results = 0
        counter = 0

        while self.documents_to_pull(search_id) > 0:
            response = self._requests_manager.get(
                endpoint,
                params={
                    'email': self.__auth_email,
                    'query': query,
                    'page': page
                },
                max_failures=10
            )

            if not isinstance(response, requests.Response):
                self.change_limit(search_id, -counter)
                self._change_status(SearchStatus.FINISHED, search_id)
                break

            if response.status_code == 200:
                response_json = response.json()
                results_size = len(response_json['results'])

                if results_size == 0:
                    self.change_limit(search_id, -counter)
                    self._change_status(SearchStatus.FINISHED, search_id)
                    break

                responses.append(response_json)
                total_results += results_size
                counter += results_size
            else:
                logging.error(f'Error code {response.status_code}, {response.content}')
                self.change_limit(search_id, -counter)
                self._change_status(SearchStatus.FINISHED, search_id)
                break

            page += 1
            logging.debug(f'unpaywall: {total_results}')

            if counter >= self.documents_to_pull(search_id):
                self.change_limit(search_id, -counter)
                self._change_status(SearchStatus.WAITING, search_id)
                logging.info(f'Pulled {counter} docs from {self.name}. Total docs pulled: {self._documents_pulled(search_id)}')
                counter = 0

                kill = False

                while True:
                    if self._kill_signal_occurred(search_id):
                        kill = True
                        break
                    if self.documents_to_pull(search_id) > 0:
                        self._change_status(SearchStatus.WORKING, search_id)
                        break

                    time.sleep(5)

                if kill:
                    logging.info(f'Kill signal for {self.name} occurred.')
                    break

            time.sleep(2)

        logging.info(f'Terminating {self.name} client. Docs pulled: {self._documents_pulled(search_id)}. Docs left: {self.documents_to_pull(search_id)}')
        self._terminate(search_id)
        return responses

    def _create_search(self, search_id: UUID, limit: int):
        super(UnpaywallClient, self)._create_search(search_id, limit)

    def _change_status(self, status: SearchStatus, search_id: UUID):
        super(UnpaywallClient, self)._change_status(status, search_id)

    def _terminate(self, search_id: UUID):
        super(UnpaywallClient, self)._terminate(search_id)

    def _documents_pulled(self, search_id: UUID) -> int:
        return super(UnpaywallClient, self)._documents_pulled(search_id)

    def _kill_signal_occurred(self, search_id: UUID):
        return super(UnpaywallClient, self)._kill_signal_occurred(search_id)

    # note: don't call this manually
    def send_kill_signal(self, search_id: UUID):
        super(UnpaywallClient, self).send_kill_signal(search_id)

    def documents_to_pull(self, search_id: UUID) -> int:
        return super(UnpaywallClient, self).documents_to_pull(search_id)

    def change_limit(self, search_id: UUID, delta: int):
        super(UnpaywallClient, self).change_limit(search_id, delta)
