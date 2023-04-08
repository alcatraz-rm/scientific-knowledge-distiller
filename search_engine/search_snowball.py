
# paper_id - id from arxiv or semantic scholar
# id_type - arxiv id, semantic scholar id or doi
import json
import logging

from deduplication import Deduplicator
from distiller.distiller import Distiller
from search_engine import Search
from search_engine.databases import SemanticScholarClient
from search_engine.databases.database_client import SupportedSources


def get_relevant_snowball_method(paper_id='', id_type='arxiv', limit: int = 1000, top_pubs_number: int = 100, remove_without_title: bool = True):
    if id_type == 'arxiv':
        paper_id = f'arXiv:{paper_id}'
    semantic_scholar_client = SemanticScholarClient()
    paper = semantic_scholar_client.get_paper(paper_id)

    assert paper, f"Can't find paper with id {paper_id}"

    citations = list(semantic_scholar_client.get_citations(paper_id))
    refs = list(semantic_scholar_client.get_references(paper_id))
    layer_1 = citations + refs

    s = Search(paper.title, limit=limit, sources=(
        SupportedSources.ARXIV,
        SupportedSources.CORE,
        SupportedSources.CROSSREF,
        SupportedSources.INTERNET_ARCHIVE,
        SupportedSources.SEMANTIC_SCHOLAR,
        SupportedSources.UNPAYWALL,
        SupportedSources.OPENALEX,
        SupportedSources.PAPERS_WITH_CODE,
    ))
    s.perform()
    results = list(s.results())
    results += layer_1
    deduplicator = Deduplicator()
    results = list(deduplicator.deduplicate(remove_without_title, results))

    distiller = Distiller()
    logging.info(f'total results after deduplication: {len(results)}')
    top = distiller.get_top_n_specter(results, paper=paper, n=top_pubs_number)

    return top


top_pubs = get_relevant_snowball_method(
    paper_id='1705.10311',
    id_type='arxiv',
    limit=10000,
    top_pubs_number=1000
)
top_pubs = [pub.to_dict() for pub in top_pubs]
for n in range(len(top_pubs)):
    top_pubs[n]['rank'] = n

with open('results.json', 'w', encoding='utf-8') as file:
    json.dump(top_pubs, file, indent=4)
