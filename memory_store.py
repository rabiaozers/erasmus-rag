"""Chunks and their embeddings kept in memory: used by the public demo, which has no PostgreSQL.
1,861 chunks x 384 numbers is small enough to search with one matrix multiplication."""
import json

import numpy as np


class MemoryStore:
    """Same interface as db.PgStore: vector_search() and all_chunks()."""

    def __init__(self, chunks_path, embeddings_path):
        with open(chunks_path, encoding="utf-8") as f:
            self.rows = [tuple(row) for row in json.load(f)]           # (source, page, content)
        self.embeddings = np.load(embeddings_path).astype(np.float32)  # one normalized vector per chunk

    def vector_search(self, query_embedding, k):
        similarities = self.embeddings @ query_embedding               # cosine, because vectors are normalized
        best = np.argsort(similarities)[::-1][:k]
        return [(*self.rows[i], float(similarities[i])) for i in best]

    def keyword_search(self, question, k):
        raise NotImplementedError("PostgreSQL full-text search is only available with PgStore")

    def all_chunks(self):
        return self.rows
