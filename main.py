# from search_engine.databases import GoogleScholarClient
import os
from pprint import pprint

import requests

from search_engine import databases, Search
from deduplication import Deduplicator
from search_engine.databases.database_client import SupportedSources
from search_engine.databases.google_scholar_client import GoogleScholarClient

gs_client = GoogleScholarClient()
for pub in gs_client.search_publications('topology'):
    print(pub)
# ss_client = databases.SematicScholarClient()
# core_client = databases.CoreClient()
# unpaywall_client = databases.UnpaywallClient()
# arxiv_client = databases.ArXivClient()
# ia_client = databases.InternetArchiveClient()

# query = 'neutral differential equations with periodic coefficients'
# crossref = databases.CrossrefClient()
# for pub in crossref.search_publications(query, limit=2000):
#     print(pub)
#
# d = Deduplicator()
# deduped_pubs = list(
#     d.deduplicate(
#         gs_client.search_publications(query, limit=5000),
        # ia_client.search_publications(query, limit=10000),
        # unpaywall_client.search_publications(query, limit=10000),
        # core_client.search_publications(query, limit=10000),
        # ss_client.search_publications(query, limit=10000),
        # arxiv_client.search_publications(query, limit=10000)
    # )
# )
# print(len(deduped_pubs))

# s = Search(query, limit=5000)
# s.perform()
# print(len(list(s.results())))

