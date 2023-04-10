import logging
import time
from typing import Iterator
from uuid import UUID

from search_engine.databases.database_client import DatabaseClient, Document, SupportedSources, SearchStatus
from utils.requests_manager import RequestsManager


class InternetArchiveClient(DatabaseClient):
    MAX_LIMIT = 500

    def __init__(self):
        self._headers = {'accept': 'application/json'}
        self._api_endpoint = 'https://scholar.archive.org/search'
        self._requests_manager = RequestsManager()

        super().__init__(SupportedSources.INTERNET_ARCHIVE)

    def search_publications(self, query: str, search_id: UUID, limit: int = 100) -> Iterator[Document]:
        self._create_search(search_id, limit)
        responses = self.__query_api(query, search_id=search_id)

        documents_pulled = self._documents_pulled(search_id)
        counter = 0
        result = []

        for response in responses:
            for raw_pub in response.get('results'):
                result.append(
                    Document(raw_pub, source=SupportedSources.INTERNET_ARCHIVE))
                counter += 1

                if counter == documents_pulled:
                    break

        return result

    def __query_api(self, query: str, search_id: UUID = ''):
        responses = []
        offset = 0
        counter = 0

        while self.documents_to_pull(search_id) > 0:
            limit_ = min(InternetArchiveClient.MAX_LIMIT,
                         self.documents_to_pull(search_id) - counter)
            query_params = {'q': query, 'limit': limit_, 'offset': offset}

            response = self._requests_manager.get(self._api_endpoint, params=query_params, headers=self._headers,
                                                  max_failures=10)

            if not response:
                self.change_limit(search_id, -counter)
                self._change_status(SearchStatus.FINISHED, search_id)
                break

            if response.status_code == 200:
                response_json = response.json()
                results_size = len(response_json.get('results', []))
                if results_size == 0:
                    self.change_limit(search_id, -counter)
                    self._change_status(SearchStatus.FINISHED, search_id)
                    break

                responses.append(response_json)
                offset += results_size
                counter += results_size

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
            else:
                logging.error(
                    f'Error code {response.status_code}, {response.content}')
                self.change_limit(search_id, -counter)
                self._change_status(SearchStatus.FINISHED, search_id)
                break

            time.sleep(2)
            logging.debug(f'internet archive: {offset}')

        logging.info(
            f'Terminating {self.name} client. Docs pulled: {self._documents_pulled(search_id)}.'
            f'Docs left: {self.documents_to_pull(search_id)}'
        )
        self._terminate(search_id)
        return responses

    def _create_search(self, search_id: UUID, limit: int):
        super(InternetArchiveClient, self)._create_search(search_id, limit)

    def _change_status(self, status: SearchStatus, search_id: UUID):
        super(InternetArchiveClient, self)._change_status(status, search_id)

    def _terminate(self, search_id: UUID):
        super(InternetArchiveClient, self)._terminate(search_id)

    def _documents_pulled(self, search_id: UUID) -> int:
        return super(InternetArchiveClient, self)._documents_pulled(search_id)

    def _kill_signal_occurred(self, search_id: UUID):
        return super(InternetArchiveClient, self)._kill_signal_occurred(search_id)

    def _wait(self, search_id: UUID):
        return super(InternetArchiveClient, self)._wait(search_id)

    # note: don't call this manually
    def send_kill_signal(self, search_id: UUID):
        super(InternetArchiveClient, self).send_kill_signal(search_id)

    def documents_to_pull(self, search_id: UUID) -> int:
        return super(InternetArchiveClient, self).documents_to_pull(search_id)

    def change_limit(self, search_id: UUID, delta: int):
        super(InternetArchiveClient, self).change_limit(search_id, delta)
