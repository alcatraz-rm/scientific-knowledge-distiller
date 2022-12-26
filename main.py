# from search_engine.databases import GoogleScholarClient
from search_engine import databases

# gs_client = GoogleScholarClient()
# gs_client.search_publications('blockchain')

ss_client = databases.SematicScholarClient()
for pub in ss_client.search_publications('topology', limit=10):
    print(pub)

print()

core_client = databases.CoreClient()
for p in core_client.search_publications('topology', limit=10):
    print(p)
