import logging
import threading
import time
from copy import deepcopy
from itertools import chain
from typing import Iterable, Tuple

from deduplication import Deduplicator
from search_engine import databases
from search_engine.databases.database_client import SupportedSources, SearchResult

logging.basicConfig(level=20)


class Search:
    def __init__(
            self,
            query: str,
            limit: int = 1000,
            remove_duplicates: bool = True,
            sources: tuple = (
                    SupportedSources.ARXIV,
                    SupportedSources.CORE,
                    SupportedSources.INTERNET_ARCHIVE,
                    SupportedSources.SEMANTIC_SCHOLAR,
                    SupportedSources.UNPAYWALL,
                    SupportedSources.CROSSREF,
                    # SupportedSources.GOOGLE_SCHOLAR
            )
    ):
        assert query, 'Query cannot be empty'
        assert limit > 0, 'Limit must be greater then zero'
        assert sources, 'Pass at least one source'

        self._results = None
        self._results_list = []

        self._query = query
        self._limit = limit
        self._remove_duplicates = remove_duplicates
        self._deduplicator = Deduplicator()

        self._clients = []
        # if SupportedSources.GOOGLE_SCHOLAR in sources:
        #     self._clients.append(databases.GoogleScholarClient())
        if SupportedSources.ARXIV in sources:
            self._clients.append(databases.ArXivClient())
        if SupportedSources.CORE in sources:
            self._clients.append(databases.CoreClient())
        if SupportedSources.INTERNET_ARCHIVE in sources:
            self._clients.append(databases.InternetArchiveClient())
        if SupportedSources.SEMANTIC_SCHOLAR in sources:
            self._clients.append(databases.SematicScholarClient())
        if SupportedSources.UNPAYWALL in sources:
            self._clients.append(databases.UnpaywallClient())
        if SupportedSources.CROSSREF in sources:
            self._clients.append(databases.CrossrefClient())
        if SupportedSources.DBLP in sources:
            self._clients.append(databases.DBLPClient())

    def perform(self):
        threads = []
        for client in self._clients:
            threads.append(threading.Thread(target=self._search, args=(deepcopy(client),)))

        for thread in threads:
            thread.start()

        for thread in threads:
            while thread.is_alive():
                time.sleep(0.1)

            thread.join()

        # self._results = chain(*[client.search_publications(self._query, self._limit) for client in self._clients])
        self._results = self._results_list

        if self._remove_duplicates:
            self._deduplicate()

    def results(self) -> Iterable[SearchResult]:
        return self._results

    def _search(self, client):
        result = list(client.search_publications(self._query, self._limit))

        with threading.Lock():
            self._results_list.extend(result)

    def _deduplicate(self):
        self._results = self._deduplicator.deduplicate(self._results)
