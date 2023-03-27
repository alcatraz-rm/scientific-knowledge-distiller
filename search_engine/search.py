import logging
import threading
import time
import uuid
from copy import deepcopy
from itertools import chain
from typing import Iterable, Tuple

from deduplication import Deduplicator
from search_engine import databases
from search_engine.databases.database_client import SupportedSources, SearchResult, SearchStatus

logging.basicConfig(level=20)


class Search:
    def __init__(
            self,
            query: str,
            limit: int = 1000,
            remove_duplicates: bool = True,
            remove_without_title: bool = True,
            sources: tuple = (
                    SupportedSources.ARXIV,
                    SupportedSources.CORE,
                    SupportedSources.INTERNET_ARCHIVE,
                    SupportedSources.SEMANTIC_SCHOLAR,
                    SupportedSources.UNPAYWALL,
                    SupportedSources.CROSSREF,
                    SupportedSources.OPENALEX,
                    SupportedSources.PAPERS_WITH_CODE,
                    # SupportedSources.GOOGLE_SCHOLAR
            )
    ):
        assert query, 'Query cannot be empty'
        assert limit >= len(sources), 'Limit must be greater then sources number'
        assert sources, 'Pass at least one source'

        self._remove_without_title = remove_without_title
        self._search_id = uuid.uuid4()

        self._results = None
        self._results_list = []

        self._query = query
        self._remove_duplicates = remove_duplicates
        self._deduplicator = Deduplicator()

        self._clients = []
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
        # if SupportedSources.DBLP in sources:
        #     self._clients.append(databases.DBLPClient())
        if SupportedSources.OPENALEX in sources:
            self._clients.append(databases.OpenAlexClient())
        if SupportedSources.PAPERS_WITH_CODE in sources:
            self._clients.append(databases.PapersWithCodeClient())

        self._limit = limit // len(sources)

    def perform(self):
        threads = {}
        active_clients = {}

        for n, client in enumerate(self._clients):
            active_clients[n] = client
            threads[n] = threading.Thread(target=self._search, args=(client,))

        for thread_index in threads:
            threads[thread_index].start()

        while True:
            clients_to_remove = []
            threads_to_remove = []
            docs_to_distribute = 0

            if len(active_clients) == 0:
                for thread_index in threads:
                    while threads[thread_index].is_alive():
                        time.sleep(1)
                    threads[thread_index].join()
                break
            all_active_clients_are_waiting = True
            for client_index in active_clients:
                if active_clients[client_index].search_status(self._search_id) != SearchStatus.WAITING:
                    all_active_clients_are_waiting = False
            if all_active_clients_are_waiting:
                for client_index in active_clients:
                    active_clients[client_index].send_kill_signal(self._search_id)

                for thread_index in threads:
                    while threads[thread_index].is_alive():
                        time.sleep(1)
                    threads[thread_index].join()
                break

            for index in active_clients:
                status = active_clients[index].search_status(self._search_id)

                if status == SearchStatus.FINISHED:
                    docs_to_distribute += active_clients[index].documents_to_pull(self._search_id)
                    clients_to_remove.append(index)
            for index in clients_to_remove:
                del active_clients[index]

            if docs_to_distribute > len(active_clients):
                docs_for_active_client = docs_to_distribute // len(active_clients)

                for client_index in active_clients:
                    active_clients[client_index].change_limit(self._search_id, docs_for_active_client)

            for thread_index in threads:
                if not threads[thread_index].is_alive():
                    threads[thread_index].join()
                    threads_to_remove.append(thread_index)
            for index in threads_to_remove:
                del threads[index]

            time.sleep(2)

        self._results = self._results_list

        total_documents = 0
        for client in self._clients:
            pulled = client._documents_pulled(self._search_id)
            logging.info(f'{client.name}: {pulled}')
            total_documents += pulled
        logging.info(f'total documents: {total_documents}')

        if self._remove_duplicates:
            self._deduplicate()

    def results(self) -> Iterable[SearchResult]:
        return self._results

    def _search(self, client):
        result = list(client.search_publications(self._query, self._search_id, self._limit))

        with threading.Lock():
            self._results_list.extend(result)

    def _deduplicate(self):
        self._results = self._deduplicator.deduplicate(self._remove_without_title, self._results)
