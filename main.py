# from search_engine.databases import GoogleScholarClient
import os

from search_engine import databases
from deduplication import Deduplicator

# gs_client = GoogleScholarClient()
# gs_client.search_publications('blockchain')

ss_client = databases.SematicScholarClient()
# for pub in ss_client.search_publications('topology', limit=10):
#     print(pub.to_csv())

# print()
#
core_client = databases.CoreClient()
# for p in core_client.search_publications('topology', limit=100):
#     print(p.to_csv())

path_to_csv = os.path.join(os.getcwd(), 'csv_result.csv')
d = Deduplicator()
deduped_pubs = list(d.deduplicate(ss_client.search_publications('topology', limit=10000),
                                  core_client.search_publications('topology', limit=10000)))
print(len(deduped_pubs))
