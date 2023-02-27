# from search_engine.databases import GoogleScholarClient
import os
from pprint import pprint

import requests

from search_engine import databases, Search
from deduplication import Deduplicator
from search_engine.databases.database_client import SupportedSources

query = input('query: ')
limit = int(input('limit: '))

# TODO: add logging to file
s = Search(query, limit=limit, sources=(
    SupportedSources.ARXIV,
    SupportedSources.CROSSREF,
    SupportedSources.INTERNET_ARCHIVE,
    SupportedSources.SEMANTIC_SCHOLAR,
    SupportedSources.UNPAYWALL,
))
s.perform()
print(len(list(s.results())))
