"""Measure retrieval: is the right page among the top-k chunks? Compare retrieval methods."""
import pandas as pd
from sentence_transformers import CrossEncoder, SentenceTransformer

from db import connect
from ingest import MODEL_NAME
from metrics import parse_pages
from retrieval import RERANKER_NAME, BM25Index, retrieve

KS = (1, 3, 5)
METHODS = ("embedding", "bm25", "hybrid", "rerank")


def evaluate(conn, model, bm25, reranker, questions, method, verbose=False):
    """Return {k: recall@k} for one retrieval method."""
    hits = {k: 0 for k in KS}
    for _, q in questions.iterrows():
        correct_pages = parse_pages(q["pages"])
        rows = retrieve(conn, model, q["question"], k=max(KS), method=method, bm25=bm25, reranker=reranker)
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
    conn = connect()
    bm25 = BM25Index(conn)
    reranker = CrossEncoder(RERANKER_NAME, device="cpu")

    results = {}
    for method in METHODS:
        print(f"\n--- {method} ---")
        results[method] = evaluate(conn, model, bm25, reranker, questions, method, verbose=True)

    print(f"\n{'method':<14}" + "".join(f"  recall@{k}" for k in KS))
    for method, r in results.items():
        print(f"{method:<14}" + "".join(f"  {r[k]:>8.2f}" for k in KS))
