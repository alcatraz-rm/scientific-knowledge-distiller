from typing import Iterator

from scholarly import scholarly, ProxyGenerator

from search_engine.databases.database import DatabaseClient, SearchResult


class GoogleScholarClient(DatabaseClient):
    def __init__(self):
        super().__init__()

    def search_publications(self, query: str) -> Iterator[SearchResult]:
        pg = ProxyGenerator()
        assert pg.FreeProxies()
        scholarly.use_proxy(pg)

        for citation in scholarly.search_pubs('blockchain'):
            print(citation)
