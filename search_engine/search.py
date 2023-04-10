import logging
import threading
import time
import uuid
from copy import deepcopy
from typing import Iterable

from progressbar import progressbar

from deduplication import Deduplicator
from search_engine import databases
from search_engine.databases import SemanticScholarClient
from search_engine.databases.database_client import SupportedSources, Document, SearchStatus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ])


class Search:
    def __init__(
            self,
            query: str,
            limit: int = 1000,
            remove_duplicates: bool = True,
            remove_without_title: bool = True,
            fill_abstracts: bool = True,
            sources: tuple = (
                SupportedSources.ARXIV,
                SupportedSources.CORE,
                SupportedSources.INTERNET_ARCHIVE,
                SupportedSources.SEMANTIC_SCHOLAR,
                SupportedSources.UNPAYWALL,
                SupportedSources.CROSSREF,
                SupportedSources.OPENALEX,
                SupportedSources.PAPERS_WITH_CODE,
            )
    ):
        assert query, 'Query cannot be empty'
        assert limit >= len(
            sources), 'Limit must be greater then sources number'
        assert sources, 'Pass at least one source'

        self._remove_without_title = remove_without_title
        self._fill_abstracts = fill_abstracts
        self._search_id = uuid.uuid4()

        logging.info(f'Search {self._search_id} created.')
        logging.info(f'Search query: {query}')
        logging.info(f'Search limit: {limit}')
        logging.info(
            f'Sources: {",".join([str(source) for source in sources])}')

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
            self._clients.append(databases.SemanticScholarClient())
        if SupportedSources.UNPAYWALL in sources:
            self._clients.append(databases.UnpaywallClient())
        if SupportedSources.CROSSREF in sources:
            self._clients.append(databases.CrossrefClient())
        if SupportedSources.OPENALEX in sources:
            self._clients.append(databases.OpenAlexClient())
        if SupportedSources.PAPERS_WITH_CODE in sources:
            self._clients.append(databases.PapersWithCodeClient())

        self._limit_for_source = limit // len(sources)
        logging.info(f'Initial limit for source: {self._limit_for_source}')

    def perform(self):
        threads = {}
        active_clients = {}

        for n, client in enumerate(self._clients):
            active_clients[n] = client
            threads[n] = threading.Thread(
                target=self._search, args=(client,), name=str(client.name))

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
                    active_clients[client_index].send_kill_signal(
                        self._search_id)

                for thread_index in threads:
                    while threads[thread_index].is_alive():
                        time.sleep(1)
                    threads[thread_index].join()
                break

            for index in active_clients:
                status = active_clients[index].search_status(self._search_id)

                if status == SearchStatus.FINISHED:
                    docs_to_distribute += active_clients[index].documents_to_pull(
                        self._search_id)
                    clients_to_remove.append(index)
            for index in clients_to_remove:
                del active_clients[index]

            if docs_to_distribute > len(active_clients):
                docs_for_active_client = docs_to_distribute // len(
                    active_clients)
                logging.info(
                    f'Found {docs_to_distribute} docs to distribute. Docs for each client: {docs_for_active_client}')

                for client_index in active_clients:
                    active_clients[client_index].change_limit(
                        self._search_id, docs_for_active_client)

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

        # trying to fill abstract
        if self._fill_abstracts:
            self._results = self._pull_abstracts()

    def results(self) -> Iterable[Document]:
        return self._results

    def _search(self, client):
        result = list(client.search_publications(
            self._query, self._search_id, self._limit_for_source))
        with threading.Lock():
            self._results_list.extend(result)

    def _pull_abstracts(self) -> Iterable[Document]:
        final_results = []
        can_have_abstract_dict = {}
        dois_list = []
        semantic_scholar_client = SemanticScholarClient()
        found = 0

        for pub in list(self._results):
            if pub.abstract or (not pub.doi) or pub.source == SupportedSources.SEMANTIC_SCHOLAR:
                final_results.append(pub)
            else:
                ss_in_sources = False
                for v in pub.versions:
                    if v['source'] == SupportedSources.SEMANTIC_SCHOLAR:
                        final_results.append(pub)
                        ss_in_sources = True
                        break

                if ss_in_sources:
                    continue
                doi = pub.doi.lower()
                can_have_abstract_dict[doi] = pub
                dois_list.append(doi)

        batches = []
        if len(dois_list) >= 50:
            batch_size = 50
        else:
            batch_size = len(dois_list)
        batches_number = 0

        for i in range(0, len(dois_list), batch_size):
            rest = len(dois_list) - batches_number * batch_size
            if rest < batch_size:
                batch_size = rest
                batches.append(dois_list[i:i + batch_size])
                break
            batches.append(dois_list[i:i + batch_size])
            batches_number += 1

        logging.info(
            'Trying to find abstracts for papers on semantic scholar...')
        retrieved_papers = []
        for batch in progressbar(batches):
            retrieved_papers += semantic_scholar_client.get_papers_batch(batch)

        for paper in retrieved_papers:
            doi = paper.doi.lower()
            other_version = can_have_abstract_dict[doi]
            if paper.abstract:
                paper.set_versions_raw(other_version.versions)
                paper.add_version(other_version)
                final_results.append(deepcopy(paper))
                found += 1
                dois_list.remove(doi)
                del can_have_abstract_dict[doi]
            else:
                other_version.add_version(deepcopy(paper))
                final_results.append(other_version)

        logging.info(f'Abstract was found for {found} papers.')

        return final_results

    def _deduplicate(self):
        self._results = self._deduplicator.deduplicate(
            self._remove_without_title, self._results)
