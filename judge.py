"""The auditor: a second LLM grades the assistant's answers without knowing how they were made.

For every answered question it sees the question, the reference answer from eval/questions.csv,
the assistant's answer and the text of the pages the assistant cited, and returns two verdicts:
  correctness: correct | partial | incorrect   (compared with the reference answer)
  grounded:    true | false                     (do the cited pages really support the answer?)

Usage:  python judge.py eval/answers_qwen2.5-3b.csv [more answer files ...]
Writes eval/judged_<name>.csv next to each input and prints a summary.
The judge runs on Groq (JUDGE_MODEL, default openai/gpt-oss-120b). When it grades answers written by the
same model, it may be too kind to itself: check a sample of verdicts by hand (see README).
"""
import json
import os
import sys
import time
from pathlib import Path

os.environ["LLM_BACKEND"] = "groq"                     # the judge always runs on Groq
os.environ["LLM_MODEL"] = os.environ.get("JUDGE_MODEL", "openai/gpt-oss-120b")

import pandas as pd  # noqa: E402

import rag  # noqa: E402
from metrics import parse_pages, summarize_verdicts  # noqa: E402

PAGE_CHARS = 2500        # text per cited page given to the judge (keeps each call under the free-tier limit)

JUDGE_PROMPT = """You are a strict grader for a question-answering system about the Erasmus+ programme.
You get a question, a REFERENCE answer written by a person who checked the source documents,
the SYSTEM answer, and the text of the pages the system cited.

1. correctness: compare the SYSTEM answer with the REFERENCE answer.
   "correct"   = same key facts (numbers, dates, conditions); wording may differ; extra correct detail is fine
   "partial"   = some key facts right, but an important part is missing or vague
   "incorrect" = a key fact is wrong (e.g. a different amount or date), or it answers a different question
2. grounded: true if the cited pages contain the facts the SYSTEM answer states; false if the answer
   states facts that are not in the cited pages.

Reply with JSON only: {"correctness": "...", "grounded": true/false, "reason": "<one short sentence>"}"""


def load_pages(chunks_path="demo/chunks.json"):
    """(source, page) -> the text of that page, rebuilt from its chunks."""
    with open(chunks_path, encoding="utf-8") as f:
        rows = json.load(f)
    pages = {}
    for source, page, content in rows:
        pages.setdefault((source, page), []).append(content)
    return {key: " ".join(parts) for key, parts in pages.items()}


def judge_one(row, pages):
    """Return the verdict for one answered question as a dict."""
    cited = parse_pages(row["cited"])
    cited_text = "\n\n".join(
        f"[{source}, page {page}]\n{pages.get((source, page), '')[:PAGE_CHARS]}" for source, page in sorted(cited)
    ) or "(no pages cited)"
    prompt = (f"QUESTION: {row['question']}\n\nREFERENCE ANSWER: {row['expected']}\n\n"
              f"SYSTEM ANSWER: {row['generated']}\n\nCITED PAGES:\n{cited_text}")
    reply = json.loads(rag.chat(JUDGE_PROMPT, prompt, schema={"type": "object"}))
    return {"correctness": str(reply.get("correctness", "")).lower(),
            "grounded": bool(reply.get("grounded")),
            "reason": str(reply.get("reason", ""))[:300]}


def judge_file(path, pages):
    answers = pd.read_csv(path)
    verdicts = []
    for _, row in answers.iterrows():
        if row["type"] == "none":                       # nothing to grade: the right behaviour is to refuse
            verdict = {"correctness": "refused" if not row["found"] else "answered_unanswerable",
                       "grounded": None, "reason": "question not covered by the documents"}
        elif not row["found"]:                          # the system said it could not find the answer
            verdict = {"correctness": "no_answer", "grounded": None, "reason": "system said not found"}
        else:
            time.sleep(8)                               # free tier: ~8,000 tokens per minute
            verdict = judge_one(row, pages)
        verdicts.append(verdict)
        print(f"{row['id']:>3}  {verdict['correctness']:<22} grounded={verdict['grounded']!s:<5}  {verdict['reason'][:70]}",
              flush=True)

    judged = pd.concat([answers, pd.DataFrame(verdicts)], axis=1)
    out = Path(path).with_name(Path(path).name.replace("answers_", "judged_"))
    judged.to_csv(out, index=False)
    print(f"\n--- {Path(path).name}  (judge: {rag.LLM_MODEL}) -> {out}")
    for line in summarize_verdicts(judged):
        print(line)
    print()


if __name__ == "__main__":
    pages = load_pages()
    for answer_file in sys.argv[1:] or ["eval/answers_qwen2.5-3b.csv"]:
        judge_file(answer_file, pages)
