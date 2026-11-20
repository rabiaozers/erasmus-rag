"""Answer a question: retrieve chunks, then let the local LLM (Ollama) write a cited answer."""
import json
import os

import requests
from pydantic import BaseModel

from retrieval import retrieve

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen2.5:3b")     # chosen over llama3.2:3b on the evaluation set
TOP_K = 5                      # chunks given to the LLM (5 x ~200 tokens fits easily in 4096)
NOT_FOUND = "I could not find this in the Erasmus+ Programme Guide or the IGU documents."

SYSTEM_PROMPT = """You answer questions about the Erasmus+ programme.
Answer ONLY with information from the numbered passages below. Do not use your own knowledge.
If the passages do not contain the answer, write "not found" and set "found" to false.
Keep the answer short (1-4 sentences) and keep exact numbers, amounts and dates as written.
In "citations", list the numbers of the passages you used."""


class LLMAnswer(BaseModel):
    """The JSON shape the LLM must return (Ollama enforces it with the schema).
    Field order matters: the model writes the answer first and decides `found` LAST,
    after it has seen what it wrote."""
    answer: str
    citations: list[int]
    found: bool


def build_prompt(question, rows):
    """Number every passage so the model can cite it: [1] (programme-guide-2027, page 80) ..."""
    passages = "\n\n".join(
        f"[{i}] ({source}, page {page})\n{content}" for i, (source, page, content, _score) in enumerate(rows, start=1)
    )
    return f"Passages:\n\n{passages}\n\nQuestion: {question}"


def ask_llm(prompt):
    """Call Ollama's chat API and parse the structured JSON answer."""
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": LLM_MODEL,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            "format": LLMAnswer.model_json_schema(),   # structured output: the reply must match this schema
            "stream": False,
            "options": {"temperature": 0, "num_ctx": 4096},
        },
        timeout=300,
    )
    response.raise_for_status()
    return LLMAnswer.model_validate(json.loads(response.json()["message"]["content"]))


def answer(conn, model, bm25, reranker, question):
    """Full RAG pipeline: retrieve -> rerank -> generate. Returns a dict ready for the API."""
    rows = retrieve(conn, model, question, k=TOP_K, method="rerank", bm25=bm25, reranker=reranker)
    llm = ask_llm(build_prompt(question, rows))

    # Turn passage numbers back into (source, page); ignore numbers the model invented.
    sources = []
    for n in llm.citations:
        if 1 <= n <= len(rows):
            source, page = rows[n - 1][0], rows[n - 1][1]
            if {"source": source, "page": page} not in sources:
                sources.append({"source": source, "page": page})
    # When the model says the passages do not answer the question, we do not trust its free text either:
    # a small model may still "explain" something loosely related. Return a fixed message instead.
    text = llm.answer
    says_not_found = any(phrase in text.lower() for phrase in ("not found", "no answer", "do not cover", "not mentioned"))
    if says_not_found:                       # the flag and the text disagree: trust the text
        llm.found = False
    if not llm.found:
        sources, text = [], NOT_FOUND

    return {
        "question": question,
        "found": llm.found,
        "answer": text,
        "sources": sources,
        "retrieved": [{"source": r[0], "page": r[1], "score": round(r[3], 3)} for r in rows],
    }


if __name__ == "__main__":
    import sys

    from sentence_transformers import CrossEncoder, SentenceTransformer

    from db import connect
    from ingest import MODEL_NAME
    from retrieval import RERANKER_NAME, BM25Index

    question = " ".join(sys.argv[1:]) or "How much monthly grant does IGU pay for a traineeship in Italy?"
    conn = connect()
    result = answer(conn, SentenceTransformer(MODEL_NAME, device="cpu"), BM25Index(conn),
                    CrossEncoder(RERANKER_NAME, device="cpu"), question)
    print(json.dumps(result, indent=2, ensure_ascii=False))
