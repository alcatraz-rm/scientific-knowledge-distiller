# from search_engine.databases import GoogleScholarClient
import csv
import json
import os
from pprint import pprint

import pdfkit
import requests
from json2html import json2html

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
), remove_without_title=False)
# s.perform()

# with open('results.csv', 'w', encoding='utf-8') as file:
#     for n, pub in enumerate(s.results()):
#         if len(pub.versions) > 0:
#             print(pub.title)
# s = Search(query, limit=limit, sources=(
#     SupportedSources.OPENALEX,
# ))
s.perform()

results = sorted(list(s.results()), key=lambda x: x.title)
res_json = [pub.to_dict() for pub in results]
config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')
with open('deduplication/cases/case-1/result.json', 'w', encoding='utf-8') as file:
    json.dump(res_json, file, indent=4)
# pdfkit.from_string(json2html.convert(res_json), 'results.pdf', configuration=config, css='style.css', options={'page-height': '297mm', 'page-width': '420mm'})

print(len(results))
