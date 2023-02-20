import os
from copy import deepcopy
from pprint import pprint
from typing import Iterator
from urllib.parse import urlencode

from scholarly import scholarly, ProxyGenerator
from fp.fp import FreeProxy
from serpapi import GoogleSearch

from search_engine.databases.database_client import DatabaseClient, SearchResult, SupportedSources


class GoogleScholarClient(DatabaseClient):
    def __init__(self):
        self._search_params = {
            'engine': 'google_scholar',
            'q': '',
            'api_key': os.getenv('SERP_API_KEY'),
            'num': 0
        }
        super().__init__()

    def search_publications(self, query: str, limit: int = 100) -> Iterator[SearchResult]:
        counter = 0

        print('----------------------------')
        print(f'Start Google Scholar search: {query}')

        pg = ProxyGenerator()
        assert pg.FreeProxies()

        # results = scholarly.search_pubs(query)

        params = deepcopy(self._search_params)
        params['q'] = query
        params['num'] = limit

        search = GoogleSearch(params)
        results = search.get_dict()

        organic_results = results["organic_results"]
        # pprint(organic_results[0])

        for result in organic_results:
            pprint(result)
            r = GoogleSearch({
            'engine': 'google_scholar_cite',
            'q': result['result_id'],
            'api_key': os.getenv('SERP_API_KEY'),
            })
            pass

        while counter != limit:
            citation = next(results)
            yield SearchResult(citation, source=SupportedSources.GOOGLE_SCHOLAR)
            counter += 1
            print(f'\rgoogle scholar: {counter}', end='')
