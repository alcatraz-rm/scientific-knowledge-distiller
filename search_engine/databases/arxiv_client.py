import logging
import threading
import time
from typing import Iterator
from uuid import UUID

import arxiv

from search_engine.databases.database_client import DatabaseClient, SearchResult, SupportedSources, SearchStatus


class ArXivClient(DatabaseClient):
    def __init__(self):
        super().__init__(SupportedSources.ARXIV)

    def search_publications(self, query: str, search_id: UUID, limit: int = 100) -> Iterator[SearchResult]:
        self._create_search(search_id, limit)

        search = arxiv.Search(query=query)
        client = arxiv.Client(num_retries=30, delay_seconds=10, page_size=200)

        counter = 0
        total_results = 0
        try:
            for publication in client.results(search):
                yield SearchResult(publication, source=SupportedSources.ARXIV)
                counter += 1
                total_results += 1
                logging.info(f'arXiv: {total_results}')

                if counter == self.documents_to_pull(search_id):
                    self._change_status(SearchStatus.WAITING, search_id)
                    self.change_limit(search_id, -counter)
                    counter = 0

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

        except arxiv.UnexpectedEmptyPageError:
            pass

        self.change_limit(search_id, -counter)
        counter = 0
        self._change_status(SearchStatus.FINISHED, search_id)
        self._terminate(search_id)

    def _create_search(self, search_id: UUID, limit: int):
        super(ArXivClient, self)._create_search(search_id, limit)

    def _change_status(self, status: SearchStatus, search_id: UUID):
        super(ArXivClient, self)._change_status(status, search_id)

    def _terminate(self, search_id: UUID):
        super(ArXivClient, self)._terminate(search_id)

    def _kill_signal_occurred(self, search_id: UUID):
        return super(ArXivClient, self)._kill_signal_occurred(search_id)

    # note: don't call this manually
    def send_kill_signal(self, search_id: UUID):
        super(ArXivClient, self).send_kill_signal(search_id)

    def documents_to_pull(self, search_id: UUID) -> int:
        return super(ArXivClient, self).documents_to_pull(search_id)

    def change_limit(self, search_id: UUID, delta: int):
        super(ArXivClient, self).change_limit(search_id, delta)
