import logging
import threading
from typing import Iterator

import arxiv

from search_engine.databases.database_client import DatabaseClient, SearchResult, SupportedSources, SearchStatus


class ArXivClient(DatabaseClient):
    def __init__(self):
        super().__init__(SupportedSources.ARXIV)

    def search_publications(self, query: str, limit: int = 100, search_id: str = '') -> Iterator[SearchResult]:
        with threading.Lock():
            self._searches[search_id] = {
                'status': SearchStatus.WORKING,
                'documents_to_pull': limit,
                'kill_signal_occurred': False
            }

        search = arxiv.Search(query=query)
        client = arxiv.Client(num_retries=30, delay_seconds=10, page_size=200)

        counter = 0
        try:
            for publication in client.results(search):
                yield SearchResult(publication, source=SupportedSources.ARXIV)
                counter += 1
                logging.info(f'arXiv: {counter}')

                if counter == limit:
                    with threading.Lock():
                        self._searches[search_id]['status'] = SearchStatus.WAITING
                        self._searches[search_id]['documents_to_pull'] -= counter

                    break
        except arxiv.UnexpectedEmptyPageError:
            pass

        with threading.Lock():
            if counter < limit:
                self._searches[search_id]['status'] = SearchStatus.FINISHED_OUT_OF_DOCUMENTS
            else:
                self._searches[search_id]['status'] = SearchStatus.FINISHED
                self._searches[search_id]['documents_to_pull'] -= counter
