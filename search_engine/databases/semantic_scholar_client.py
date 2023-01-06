from pprint import pprint
from typing import Iterator

from search_engine.databases.database_client import DatabaseClient, SearchResult, SupportedSources
from semanticscholar import SemanticScholar


class SematicScholarClient(DatabaseClient):
    MAX_LIMIT = 100

    def __init__(self):
        self._sch = SemanticScholar()
        super().__init__()

    def search_publications(self, query: str, limit: int = 100) -> Iterator[SearchResult]:
        print('----------------------------')
        print(f'Start Semantic Scholar search: {query}')

        limit_ = min(limit, SematicScholarClient.MAX_LIMIT)
        results = self._sch.search_paper(query.strip(), limit=limit_)
        counter = 0
        for result in results:
            yield SearchResult(raw_data=dict(result), source=SupportedSources.SEMANTIC_SCHOLAR)
            counter += 1

            if counter == limit:
                break

            print(f'\rsemantic scholar: {counter}', end='')

        print(f'\nTotal documents found on Semantic Scholar: {counter}')
