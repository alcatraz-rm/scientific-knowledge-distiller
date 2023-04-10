import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from distiller.distiller import Distiller
from search_engine import Search
from search_engine.databases.database_client import SupportedSources
from utils.utils import find_root_directory

root_path = find_root_directory()
load_dotenv(dotenv_path=Path(os.path.join(root_path, '.env')))

query = input('query: ')
limit = int(input('limit: '))

s = Search(
    query,
    limit=limit,
    remove_duplicates=True,
    remove_without_title=True,
    fill_abstracts=True,
    sources=(
        SupportedSources.ARXIV,
        SupportedSources.CORE,
        SupportedSources.CROSSREF,
        SupportedSources.INTERNET_ARCHIVE,
        SupportedSources.SEMANTIC_SCHOLAR,
        SupportedSources.UNPAYWALL,
        SupportedSources.OPENALEX,
        SupportedSources.PAPERS_WITH_CODE,
    )
)
d = Distiller()

s.perform()
results = list(s.results())
logging.info(f'total results after deduplication: {len(results)}')

top_1000 = d.get_top_n_specter(results, query, n=1000)
top_1000 = [pub.to_dict() for pub in top_1000]
for n in range(len(top_1000)):
    top_1000[n]['rank'] = n

with open('results.json', 'w', encoding='utf-8') as file:
    json.dump(top_1000, file, indent=4)
