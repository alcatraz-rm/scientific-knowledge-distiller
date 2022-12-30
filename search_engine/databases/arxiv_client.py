from typing import Iterator

import arxiv

from search_engine.databases.database import DatabaseClient, SearchResult


class ArXivClient(DatabaseClient):
    def __init__(self):
        super().__init__()

    def search_publications(self, query: str, limit: int = 100) -> Iterator[SearchResult]:
        search = arxiv.Search(query=query, max_results=limit)

        print('----------------------------')
        print(f'Start ArXiv search: {query}')

        counter = 0
        try:
            for publication in search.results():
                yield SearchResult(publication, source='arxiv')
                counter += 1
                print(f'\rarXiv: {counter}', end='')

                if counter == limit:
                    break
        except arxiv.UnexpectedEmptyPageError:
            pass

        print(f'\nTotal documents found on ArXiv: {counter}')
