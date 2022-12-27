from pprint import pprint
from typing import Iterator

from search_engine.databases.database import DatabaseClient, SearchResult
from semanticscholar import SemanticScholar


class SematicScholarClient(DatabaseClient):
    def __init__(self):
        self._sch = SemanticScholar()
        super().__init__()

    def search_publications(self, query: str, limit: int = 100) -> Iterator[SearchResult]:
        results = self._sch.search_paper(query.strip(), limit=limit)
        for n, result in enumerate(results):
            if n == limit:
                break
            yield SearchResult(raw_data=dict(result), source='semantic_scholar')
