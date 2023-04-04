from itertools import chain
from typing import Iterable

import progressbar
import torch
from sentence_transformers import SentenceTransformer, util

from search_engine.databases.database_client import Document


class Distiller:
    def __init__(self):
        self._roberta = SentenceTransformer('stsb-roberta-large')

    def get_top_n(self, documents: Iterable[Document], query: str, n: int, method='roberta'):
    # methods: roberta, scibert, w2v
        query_embedding = self._roberta.encode(query, convert_to_tensor=True, show_progress_bar=False, normalize_embeddings=True)
        publications_dict = {pub.id: pub for pub in documents}
        result_list = []

        for pub_id in progressbar.progressbar(publications_dict):
            title = publications_dict[pub_id].title.lower()
            title_embedding = self._roberta.encode(title, convert_to_tensor=True, show_progress_bar=False, normalize_embeddings=True)
            cosine_scores = util.dot_score(query_embedding, title_embedding)
            sim_score = cosine_scores.item()
            result_list.append((pub_id, sim_score))

        top_n_docs = [publications_dict[doc[0]] for doc in sorted(result_list, key=lambda x: -x[1])[:n]]
        return top_n_docs

    def get_top_n_specter(self, documents: Iterable[Document], query: str, n: int):
        documents = list(documents)
        model = SentenceTransformer('allenai-specter')
        paper_texts = [paper.title + '[SEP]' + paper.abstract for paper in documents]
        corpus_embeddings = model.encode(paper_texts, convert_to_tensor=True, batch_size=16)
        query_embedding = model.encode(query + '[SEP]', convert_to_tensor=True)

        search_hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=n, query_chunk_size=150)[0]
        return [documents[hit['corpus_id']] for hit in search_hits]
