from typing import Iterable

from sentence_transformers import SentenceTransformer, util

from search_engine.databases.database_client import Document


class Distiller:
    def __init__(self):
        pass

    def get_top_n_roberta(self, documents: Iterable[Document], query: str, n: int):
        documents = list(documents)
        roberta = SentenceTransformer('stsb-roberta-large')
        query_embedding = roberta.encode(query, convert_to_tensor=True, show_progress_bar=False,
                                         normalize_embeddings=True)
        paper_titles = [p.title for p in documents]
        corpus_embeddings = roberta.encode(
            paper_titles, convert_to_tensor=True, batch_size=16)
        search_hits = util.semantic_search(
            query_embedding, corpus_embeddings, top_k=n, query_chunk_size=150)[0]
        return [documents[hit['corpus_id']] for hit in search_hits]

    def get_top_n_specter(self, documents: Iterable[Document], query: str = '', n: int = 100):
        documents = [p for p in documents]
        specter = SentenceTransformer('allenai-specter')
        paper_texts = []
        for p in documents:
            abstract = p.abstract if p.abstract else p.title
            paper_texts.append(p.title + '[SEP]' + abstract)
        # paper_texts = [p.title + '[SEP]' + p.abstract for p in documents]
        corpus_embeddings = specter.encode(
            paper_texts, convert_to_tensor=True, batch_size=16)
        query_embedding = specter.encode(
            query + '[SEP]' + query, convert_to_tensor=True)

        search_hits = util.semantic_search(
            query_embedding, corpus_embeddings, top_k=n, query_chunk_size=150)[0]
        return [documents[hit['corpus_id']] for hit in search_hits]
