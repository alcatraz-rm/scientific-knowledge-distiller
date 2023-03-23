# from search_engine.databases import GoogleScholarClient
import os
from pprint import pprint

import requests

from search_engine import databases, Search
from deduplication import Deduplicator
from search_engine.databases.database_client import SupportedSources

from dotenv import load_dotenv
from pathlib import Path

initial_wd = os.getcwd()
while os.path.split(os.getcwd())[-1] != 'scientific-knowledge-distiller':
    os.chdir(os.path.join(os.getcwd(), '..'))
root_path = os.getcwd()
os.chdir(initial_wd)

load_dotenv(dotenv_path=Path(os.path.join(root_path, '.env')))

query = input('query: ')
limit = int(input('limit: '))

# TODO: add logging to file
s = Search(query, limit=limit, sources=(
    SupportedSources.ARXIV,
    SupportedSources.CORE,
    SupportedSources.CROSSREF,
    SupportedSources.INTERNET_ARCHIVE,
    SupportedSources.SEMANTIC_SCHOLAR,
    SupportedSources.UNPAYWALL,
))
s.perform()

# with open('results.csv', 'w', encoding='utf-8') as file:
#     for n, pub in enumerate(s.results()):
#         if len(pub.versions) > 0:
#             print(pub.title)

print(len(list(s.results())))

# for n, pub in enumerate(s.results()):
#     if pub.lang != 'en':
#         print(pub.title, pub.lang)
