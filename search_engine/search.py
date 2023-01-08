from itertools import chain
from typing import Iterable

from deduplication import Deduplicator
from search_engine import databases
from search_engine.databases.database_client import SupportedSources, SearchResult


class Search:
    def __init__(
            self,
            query: str,
            limit: int = 1000,
            remove_duplicates: bool = True,
            sources: tuple[SupportedSources] = (
                    SupportedSources.ARXIV,
                    SupportedSources.CORE,
                    SupportedSources.INTERNET_ARCHIVE,
                    SupportedSources.SEMANTIC_SCHOLAR,
                    SupportedSources.UNPAYWALL,
                    SupportedSources.CROSSREF
            )
    ):
        assert query, 'Query cannot be empty'
        assert limit > 0, 'Limit must be greater then zero'
        assert sources, 'Pass at least one source'

        self._results = None

        self._query = query
        self._limit = limit
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

    def perform(self):
        self._results = chain(*[client.search_publications(self._query, self._limit) for client in self._clients])
        if self._remove_duplicates:
            self._deduplicate()

    def results(self) -> Iterable[SearchResult]:
        return self._results

    def _deduplicate(self):
        self._results = self._deduplicator.deduplicate(self._results)
