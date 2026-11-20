"""Evaluate the generated answers on the 34 questions and save them to eval/answers.csv.

Three automatic checks (manual reading of answers.csv is still the final judge):
  - refusal:   for questions the documents do not cover, does the system say "not found"?
  - citation:  for the other questions, does it cite at least one correct page?
  - numbers:   do the key numbers of the expected answer (750, 20, 2026 ...) appear in the generated answer?
"""
import time

import pandas as pd
from sentence_transformers import CrossEncoder, SentenceTransformer

from db import PgStore, connect
from ingest import MODEL_NAME
from metrics import numbers, parse_pages
from rag import LLM_BACKEND, LLM_MODEL, answer
from retrieval import RERANKER_NAME, BM25Index


if __name__ == "__main__":
    questions = pd.read_csv("eval/questions.csv")
    store = PgStore(connect())
    model = SentenceTransformer(MODEL_NAME, device="cpu")
    bm25 = BM25Index(store)
    reranker = CrossEncoder(RERANKER_NAME, device="cpu")

    records = []
    for _, q in questions.iterrows():
        if LLM_BACKEND == "groq":
            time.sleep(12)             # free tier: ~8,000 tokens per minute, one question uses ~1,600
        start = time.time()
        result = answer(store, model, bm25, reranker, q["question"])
        seconds = time.time() - start

        cited = {(s["source"], s["page"]) for s in result["sources"]}
        expected_numbers = numbers(q["answer"])
        record = {
            "id": q["id"], "type": q["type"], "question": q["question"],
            "expected": q["answer"], "generated": result["answer"], "found": result["found"],
            "cited": ";".join(f"{s}:{p}" for s, p in sorted(cited)), "seconds": round(seconds, 1),
        }
        if q["type"] == "none":
            record["refusal_ok"] = not result["found"]
        else:
            record["citation_ok"] = bool(cited & parse_pages(q["pages"]))
            if expected_numbers:
                record["numbers_ok"] = expected_numbers <= numbers(result["answer"])   # all key numbers present
        records.append(record)
        print(f"{q['id']:>3} {seconds:5.1f}s  found={result['found']!s:<5}  {result['answer'][:90]}")

    df = pd.DataFrame(records)
    safe_name = LLM_MODEL.replace(":", "-").replace("/", "-")        # "openai/gpt-oss-120b" -> "openai-gpt-oss-120b"
    df.to_csv(f"eval/answers_{safe_name}.csv", index=False)
    print("saved", f"eval/answers_{safe_name}.csv")

    answerable = df[df["type"] != "none"]
    print(f"\n--- summary ({LLM_MODEL}) ---")
    print(f"refusals on unanswerable questions: {int(df['refusal_ok'].sum())}/{df['refusal_ok'].notna().sum()}")
    print(f"answered (found=True):              {int(answerable['found'].sum())}/{len(answerable)}")
    print(f"cites a correct page:               {int(answerable['citation_ok'].sum())}/{len(answerable)}")
    print(f"all key numbers present:            {int(df['numbers_ok'].sum())}/{df['numbers_ok'].notna().sum()}")
    print(f"average time per question:          {df['seconds'].mean():.1f} s")
