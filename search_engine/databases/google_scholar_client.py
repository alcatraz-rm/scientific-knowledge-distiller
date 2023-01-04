import os
from pprint import pprint
from typing import Iterator
from urllib.parse import urlencode

# from scholarly import scholarly, ProxyGenerator
# from fp.fp import FreeProxy
from serpapi import GoogleSearch

from search_engine.databases.database import DatabaseClient, SearchResult, SupportedSources


class GoogleScholarClient(DatabaseClient):
    def __init__(self):
        super().__init__()

    def search_publications(self, query: str, limit: int = 100) -> Iterator[SearchResult]:
        # pg = ProxyGenerator()
        # assert pg.FreeProxies()
        # scholarly.use_proxy(pg)
        # proxy = FreeProxy(rand=True, timeout=1, country_id=['US', 'CA'], https=True).get()
        # pg = ProxyGenerator()
        # success = pg.SingleProxy(http=proxy, https=proxy)
        # print(success)
        # scholarly.use_proxy(pg)
        # scholarly.use_proxy(http=proxy, https=proxy)

        counter = 0

        print('----------------------------')
        print(f'Start Google Scholar search: {query}')
        # results = scholarly.search_pubs(query)
        # gateway = f'https://serpapi.com/search.json?engine=google_scholar&q={urlencode(query)}'

        params = {
            "engine": "google_scholar",
            "q": query,
            "api_key": os.getenv('SERP_API_KEY')
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        organic_results = results["organic_results"]
        pprint(organic_results[0])

        # while counter != limit:
        #     citation = next(results)
        #     yield SearchResult(citation, source=SupportedSources.GOOGLE_SCHOLAR)
        #     counter += 1
        #     print(f'\rgoogle scholar: {counter}', end='')
