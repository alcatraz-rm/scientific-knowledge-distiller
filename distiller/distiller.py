import os
import pickle
import re
import string
from typing import Iterable

import nltk
import numpy as np
import progressbar
import torch
from gensim.models import Doc2Vec
from sentence_transformers import SentenceTransformer, util
from transformers import AutoTokenizer, AutoModel

from search_engine.databases.database_client import Document


def preprocess_text(text, flg_stemm=False, flg_lemm=True, lst_stopwords=nltk.corpus.stopwords.words("english")):
    text = re.sub(r'[^\w\s]', '', str(text).lower().strip())

    lst_text = text.split()
    if lst_stopwords is not None:
        lst_text = [word for word in lst_text if word not in
                    lst_stopwords]
    if flg_stemm:
        ps = nltk.stem.porter.PorterStemmer()
        lst_text = [ps.stem(word) for word in lst_text]
    if flg_lemm:
        lem = nltk.stem.wordnet.WordNetLemmatizer()
        lst_text = [lem.lemmatize(word) for word in lst_text]
    text = " ".join(lst_text)
    return text


class Distiller:
    def __init__(self):
        initial_wd = os.getcwd()

        while os.path.split(os.getcwd())[-1] != 'scientific-knowledge-distiller':
            os.chdir(os.path.join(os.getcwd(), '..'))

        self._root_path = os.getcwd()
        os.chdir(initial_wd)
        self._path_to_doc2vec = os.path.join(
            self._root_path, 'distiller', 'models', 'dm_arxiv', 'dm_arxiv')
        self._path_to_tfidf_vectorizer = os.path.join(self._root_path, 'distiller', 'models', 'vectorizer.pickle')

    def get_top_n_roberta(self, documents: Iterable[Document], query: str, n: int):
        documents = list(documents)
        # stsb-roberta-large
        roberta = SentenceTransformer('all-roberta-large-v1')
        query_embedding = roberta.encode(query, convert_to_tensor=True, show_progress_bar=False,
                                         normalize_embeddings=True)
        paper_titles = []
        for p in documents:
            if p.abstract:
                paper_titles.append(f'{p.title} {p.abstract}')
            else:
                paper_titles.append(p.title)
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

    def get_top_n_specter2(self, documents: Iterable[Document], query: str = '', n: int = 100):
        documents = [p for p in documents]

        tokenizer = AutoTokenizer.from_pretrained('allenai/specter2')
        model = AutoModel.from_pretrained('allenai/specter2')
        model.load_adapter("allenai/specter2_proximity", source="hf", load_as="proximity", set_active=True)

        text_batch = []
        for p in documents:
            abstract = p.abstract if p.abstract else ''
            text_batch.append(p.title + tokenizer.sep_token + abstract)

        inputs = tokenizer(text_batch, padding=True, truncation=True,
                           return_tensors="pt", return_token_type_ids=False, max_length=512)

        output = model(**inputs)
        corpus_embeddings = output.last_hidden_state[:, 0, :]

        inputs = tokenizer(query + tokenizer.sep_token, padding=True, truncation=True,
                           return_tensors="pt", return_token_type_ids=False, max_length=512)
        output = model(**inputs)
        query_embedding = output.last_hidden_state[:, 0, :]

        search_hits = util.semantic_search(
            query_embedding, corpus_embeddings, top_k=n, query_chunk_size=150)[0]

        return [documents[hit['corpus_id']] for hit in search_hits]

    def get_top_n_doc2vec(self, documents: Iterable[Document], query: str = '', n: int = 100):
        d2v_model = Doc2Vec.load(self._path_to_doc2vec)
        documents = list(documents)
        query_embedding = torch.Tensor(d2v_model.infer_vector(query.lower().split()))
        corpus_embeddings = torch.Tensor(np.array([d2v_model.infer_vector(
            f'{paper.title} {paper.abstract}'.translate(str.maketrans('', '', string.punctuation)).lower().split()) for
            paper in documents]))
        corpus_embeddings = []
        batch_size = 1024
        i = 0
        batches_number = len(documents) // batch_size
        bar = progressbar.ProgressBar(max_value=batches_number)

        while i * batch_size <= len(documents):
            corpus_embeddings += [d2v_model.infer_vector(
                f'{paper.title} {paper.abstract}'.translate(str.maketrans('', '', string.punctuation)).lower().split())
                for
                paper in documents[i * batch_size:(i + 1) * batch_size]]
            i += 1
            bar.update(i)

        search_hits = util.semantic_search(
            query_embedding, corpus_embeddings, top_k=n, query_chunk_size=150)[0]
        return [documents[hit['corpus_id']] for hit in search_hits]

    def get_top_n_tfidf(self, documents: Iterable[Document], query: str = '', n: int = 100):
        with open(self._path_to_tfidf_vectorizer, 'rb') as dump_file:
            vectorizer = pickle.load(dump_file)

        query_embedding = torch.Tensor(vectorizer.transform([preprocess_text(query)]).toarray())

        corpus_embeddings = torch.Tensor(
            vectorizer.transform([preprocess_text(f'{doc.title} {doc.abstract}') for doc in documents]).toarray())

        search_hits = util.semantic_search(
            query_embedding, corpus_embeddings, top_k=n, query_chunk_size=150)[0]
        return [documents[hit['corpus_id']] for hit in search_hits]
