# from search_engine.databases import GoogleScholarClient
import csv
import json
import logging
import os
import time
from pprint import pprint

import pdfkit
import requests
from json2html import json2html

from distiller.distiller import Distiller
from search_engine import databases, Search
from deduplication import Deduplicator
from search_engine.databases.database_client import SupportedSources, Document

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
    SupportedSources.OPENALEX,
    SupportedSources.PAPERS_WITH_CODE,
))
d = Distiller()

start_time = time.time()
s.perform()
results = list(s.results())
logging.info(f'total results after deduplication: {len(results)}')
top_1000 = d.get_top_n_specter(results, query, 1000)
end_time = time.time()
top_1000 = [pub.to_dict() for pub in top_1000]
for n in range(len(top_1000)):
    top_1000[n]['rank'] = n

with open('results.json', 'w', encoding='utf-8') as file:
    json.dump(top_1000, file, indent=4)

logging.info(f'elapsed time: {end_time - start_time}')
# res_json = [pub.to_dict() for pub in results]
# config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')
# with open('deduplication/cases/case-1/result.json', 'w', encoding='utf-8') as file:
#     json.dump(res_json, file, indent=4)
# pdfkit.from_string(json2html.convert(res_json), 'results.pdf', configuration=config, css='style.css', options={'page-height': '297mm', 'page-width': '420mm'})

# print(len(results))
