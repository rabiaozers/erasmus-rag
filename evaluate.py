"""Measure retrieval: is the right page among the top-k chunks? Compare retrieval methods.

    python evaluate.py                                      # PostgreSQL, all methods (rerank+rewrite needs the LLM)
    STORE=memory METHODS=bm25,hybrid,rerank python evaluate.py   # the demo index, no database and no LLM
"""
import os

import pandas as pd
from sentence_transformers import CrossEncoder, SentenceTransformer

from db import PgStore, connect
from ingest import MODEL_NAME
from memory_store import MemoryStore
from metrics import parse_pages
from rag import rewrite_query
from retrieval import RERANKER_NAME, BM25Index, retrieve

KS = (1, 3, 5)
METHODS = tuple(os.getenv("METHODS", "embedding,bm25,hybrid,rerank,rerank+rewrite").split(","))


def evaluate(store, model, bm25, reranker, questions, method, verbose=False):
    """Return {k: recall@k} for one retrieval method."""
    hits = {k: 0 for k in KS}
    for _, q in questions.iterrows():
        correct_pages = parse_pages(q["pages"])
        if method == "rerank+rewrite":                          # the full pipeline of rag.py: needs the LLM
            rewritten = rewrite_query(q["question"])
            rows = retrieve(store, model, q["question"], k=max(KS), method="rerank", bm25=bm25, reranker=reranker,
                            search_queries=[q["question"], rewritten])
        else:
            rows = retrieve(store, model, q["question"], k=max(KS), method=method, bm25=bm25, reranker=reranker)
        found_pages = [(row[0], row[1]) for row in rows]      # row = (source, page, content, score)

        for k in KS:
            hit = any(p in found_pages[:k] for p in correct_pages)
            hits[k] += hit

        if verbose:
            short = lambda pairs: [("G" if s.startswith("programme") else s[4:]) + str(p) for s, p in pairs]
            print(f"{q['id']:>3} {'✓' if hit else '✗'}  correct {short(sorted(correct_pages))}  found {short(found_pages)}")
    return {k: hits[k] / len(questions) for k in KS}


if __name__ == "__main__":
    questions = pd.read_csv("eval/questions.csv")
    questions = questions[questions["type"] != "none"]        # no correct page to find
    model = SentenceTransformer(MODEL_NAME, device="cpu")
    if os.getenv("STORE") == "memory":
        store = MemoryStore("demo/chunks.json", "demo/embeddings.npy")
    else:
        store = PgStore(connect())
    bm25 = BM25Index(store)
    reranker = CrossEncoder(RERANKER_NAME, device="cpu")

    results = {}
    for method in METHODS:
        print(f"\n--- {method} ---")
        results[method] = evaluate(store, model, bm25, reranker, questions, method, verbose=True)

    print(f"\n{'method':<16}" + "".join(f"  recall@{k}" for k in KS))
    for method, r in results.items():
        print(f"{method:<16}" + "".join(f"  {r[k]:>8.2f}" for k in KS))

    for group in ("short", "turkish", "igu"):
        subset = questions[questions["type"] == group]
        print(f"\nonly the {len(subset)} {group} questions, recall@5:")
        for method in [m for m in ("rerank", "rerank+rewrite") if m in METHODS]:
            print(f"{method:<16}  {evaluate(store, model, bm25, reranker, subset, method)[5]:.2f}")
