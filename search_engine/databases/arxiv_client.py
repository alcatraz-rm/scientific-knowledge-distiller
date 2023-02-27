import logging
from typing import Iterator

import arxiv

from search_engine.databases.database_client import DatabaseClient, SearchResult, SupportedSources


class ArXivClient(DatabaseClient):
    def __init__(self):
        super().__init__()

    def search_publications(self, query: str, limit: int = 100) -> Iterator[SearchResult]:
        search = arxiv.Search(query=query)
        client = arxiv.Client(num_retries=10, delay_seconds=5, page_size=200)

        # print('----------------------------')
        # print(f'Start ArXiv search: {query}')

        counter = 0
        try:
            for publication in client.results(search):
                yield SearchResult(publication, source=SupportedSources.ARXIV)
                counter += 1
                logging.info(f'arXiv: {counter}')
                # print(f'\rarXiv: {counter}', end='')

                if counter == limit:
                    break
        except arxiv.UnexpectedEmptyPageError:
            pass

        # print(f'\nTotal documents found on ArXiv: {counter}')
