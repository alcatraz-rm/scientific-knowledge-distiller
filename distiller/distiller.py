from typing import Iterable

import progressbar
from sentence_transformers import SentenceTransformer, util

from search_engine.databases.database_client import Document


class Distiller:
    def __init__(self):
        pass

    def get_top_n_roberta(self, documents: Iterable[Document], query: str, n: int, method='roberta'):
        # methods: roberta, scibert, w2v
        publications_dict = {pub.id: pub for pub in documents}
        result_list = []
        roberta = SentenceTransformer('stsb-roberta-large')
        query_embedding = roberta.encode(query, convert_to_tensor=True, show_progress_bar=False,
                                         normalize_embeddings=True)
        paper_titles = [p.title for p in documents]
        corpus_embeddings = roberta.encode(paper_titles, convert_to_tensor=True, batch_size=16)
        search_hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=n, query_chunk_size=150)[0]
        return [documents[hit['corpus_id']] for hit in search_hits]

    def get_top_n_specter(self, documents: Iterable[Document], query: str = '', paper: Document = None, n: int = 100):
        assert (query and not paper) or (paper and not query), 'Please use query or document, not both'
        documents = list(documents)
        model = SentenceTransformer('allenai-specter')
        paper_texts = [p.title + '[SEP]' + p.abstract for p in documents]
        corpus_embeddings = model.encode(paper_texts, convert_to_tensor=True, batch_size=16)

        if query:
            query_embedding = model.encode(query + '[SEP]', convert_to_tensor=True)
        else:
            query_embedding = model.encode(paper.title + '[SEP]' + paper.abstract, convert_to_tensor=True)

        search_hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=n, query_chunk_size=150)[0]
        return [documents[hit['corpus_id']] for hit in search_hits]
