"""Ways to retrieve chunks: embedding, keyword (ts_rank), BM25, hybrid (RRF), and hybrid + reranker."""
import re

import numpy as np
import snowballstemmer
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS


RRF_K = 60          # the constant in 1 / (RRF_K + rank); the usual default
CANDIDATES = 20     # how many results each search contributes to the fusion
EMBEDDING_MODEL = "all-MiniLM-L6-v2"                     # 384 numbers per chunk; reads at most 256 tokens
RERANKER_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"   # small English cross-encoder, fine on CPU


def rrf_merge(result_lists, k):
    """Reciprocal Rank Fusion: sum 1 / (RRF_K + rank) over every list a chunk appears in."""
    scores = {}
    rows_by_key = {}
    for results in result_lists:
        for rank, row in enumerate(results, start=1):     # rank = 1, 2, 3 ...
            key = (row[1], row[2])                          # (page, content) identifies a chunk
            rows_by_key[key] = row
            scores[key] = scores.get(key, 0) + 1 / (RRF_K + rank)

    best = sorted(scores, key=scores.get, reverse=True)[:k]
    return [rows_by_key[key] for key in best]


STEMMER = snowballstemmer.stemmer("english")       # the same algorithm PostgreSQL uses


def tokenize(text):
    """Lowercase, drop stop words, reduce words to their stem:
    'What are the Youth Exchanges grants?' -> ['youth', 'exchang', 'grant']"""
    words = re.findall(r"[a-z0-9]+", text.lower())
    words = [w for w in words if w not in ENGLISH_STOP_WORDS]
    return STEMMER.stemWords(words)


class BM25Index:
    """Keyword search with IDF: rare words like 'visa' count more than common ones like 'erasmus'."""

    def __init__(self, store):
        self.rows = store.all_chunks()                                 # (source, page, content)
        self.bm25 = BM25Okapi([tokenize(row[2]) for row in self.rows])  # IDF is computed here, like fit()

    def search(self, question, k=20):
        scores = self.bm25.get_scores(tokenize(question))              # one score per chunk
        best = np.argsort(scores)[::-1][:k]                            # indices of the k highest scores
        return [(*self.rows[i], float(scores[i])) for i in best]


def rerank(reranker, question, rows, k):
    """Read (question, chunk) TOGETHER and score how well the chunk answers the question.
    Slower than embeddings, so we only apply it to the few candidates from the hybrid search."""
    pairs = [(question, row[2]) for row in rows]                 # row[2] = chunk text
    scores = reranker.predict(pairs)                             # one relevance score per pair
    results, seen_pages = [], set()
    for i in np.argsort(scores)[::-1]:
        page = rows[i][:2]                                       # (source, page)
        if page in seen_pages:                                   # one chunk per page: two chunks of the same page
            continue                                             # would push another useful page out of the top k
        seen_pages.add(page)
        results.append((*rows[i][:3], float(scores[i])))
        if len(results) == k:
            break
    return results


def retrieve(store, model, question, k=5, method="hybrid", bm25=None, reranker=None, search_queries=None):
    """Return the top-k chunks as rows (source, page, content, score).
    `store` is a PgStore (PostgreSQL, local) or a MemoryStore (public demo): both have vector_search().
    `search_queries` (hybrid and rerank only): several phrasings of the question, e.g. the original and
    a rewritten one; every phrasing is searched and all result lists are fused with RRF."""
    if method == "keyword":
        return store.keyword_search(question, k)
    if method == "bm25":
        return bm25.search(question, k)
    query = model.encode(question, normalize_embeddings=True)
    if method == "embedding":
        return store.vector_search(query, k)
    if method == "hybrid_tsrank":
        return rrf_merge([store.vector_search(query, CANDIDATES), store.keyword_search(question, CANDIDATES)], k)
    lists = []
    for q in search_queries or [question]:
        q_vector = query if q == question else model.encode(q, normalize_embeddings=True)
        lists += [store.vector_search(q_vector, CANDIDATES), bm25.search(q, CANDIDATES)]
    candidates = rrf_merge(lists, CANDIDATES)
    if method == "rerank":
        rerank_query = (search_queries or [question])[-1]          # the fullest phrasing reads best for the reranker
        return rerank(reranker, rerank_query, candidates, k)       # hybrid → 20 candidates → reranker → top k
    return candidates[:k]                                          # hybrid = embedding + BM25
