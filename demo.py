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
filename = input('filename: ')

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

top_roberta = d.get_top_n_roberta(results, query, n=100)
top_roberta = [pub.to_dict() for pub in top_roberta]
for n in range(len(top_roberta)):
    top_roberta[n]['rank'] = n

with open(f'{filename}-roberta.json', 'w', encoding='utf-8') as file:
    json.dump(top_roberta, file, indent=4)

top_specter = d.get_top_n_specter(results, query, n=100)
top_specter = [pub.to_dict() for pub in top_specter]
for n in range(len(top_specter)):
    top_specter[n]['rank'] = n

with open(f'{filename}-specter.json', 'w', encoding='utf-8') as file:
    json.dump(top_specter, file, indent=4)

