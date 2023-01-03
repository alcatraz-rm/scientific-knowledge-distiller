# from search_engine.databases import GoogleScholarClient
import os

from search_engine import databases
from deduplication import Deduplicator
from search_engine.databases.google_scholar_client import GoogleScholarClient

gs_client = GoogleScholarClient()

# for pub in gs_client.search_publications('topology', limit=100):
#     print(pub)
#     input()

ss_client = databases.SematicScholarClient()
# for pub in ss_client.search_publications('topology', limit=10):
#     print(pub.to_csv())

# print()
#
core_client = databases.CoreClient()
# for p in core_client.search_publications('topology', limit=10):
# print(p.to_csv())
unpaywall_client = databases.UnpaywallClient()
# aminer_client = databases.AminerClient()
# for pub in unpaywall_client.search_publications('random forest', limit=200):
#     print(pub)

query = 'random forest'
# for pub in aminer_client.search_publications(query, limit=200):
#     print(pub)
#
arxiv_client = databases.ArXivClient()
d = Deduplicator()
deduped_pubs = list(
    d.deduplicate(
        unpaywall_client.search_publications(query, limit=1000),
        core_client.search_publications(query, limit=1000),
        ss_client.search_publications(query, limit=1000),
        arxiv_client.search_publications(query, limit=1000),
        gs_client.search_publications(query, limit=1000)
    )
)
print(len(deduped_pubs))
