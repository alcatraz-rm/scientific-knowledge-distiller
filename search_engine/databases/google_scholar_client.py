from typing import Iterator

from scholarly import scholarly, ProxyGenerator

from search_engine.databases.database import DatabaseClient, SearchResult, SupportedSources


class GoogleScholarClient(DatabaseClient):
    def __init__(self):
        super().__init__()

    def search_publications(self, query: str, limit: int = 100) -> Iterator[SearchResult]:
        counter = 0

        print('----------------------------')
        print(f'Start Google Scholar search: {query}')

        for citation in scholarly.search_pubs(query):
            yield SearchResult(citation, source=SupportedSources.GOOGLE_SCHOLAR)
            counter += 1

            if counter == limit:
                break

            print(f'\rgoogle scholar: {counter}', end='')
