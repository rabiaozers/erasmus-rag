"""Answer a question: rewrite it, retrieve chunks, then let the LLM write a cited answer."""
import json
import os
import time
import tomllib
from pathlib import Path

import requests
from pydantic import BaseModel

from retrieval import retrieve

# Two ways to run the LLM, chosen with the LLM_BACKEND environment variable:
#   "ollama" (default): a small model on this computer's GPU, nothing leaves the machine
#   "groq": a large model through Groq's free API, used by the public demo (needs GROQ_API_KEY)
LLM_BACKEND = os.environ.get("LLM_BACKEND", "ollama")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODELS = {"ollama": "qwen2.5:3b",                 # chosen over llama3.2:3b on the evaluation set
                  "groq": "openai/gpt-oss-120b"}       # largest open model on Groq's free tier (Nov 2026)
LLM_MODEL = os.environ.get("LLM_MODEL", DEFAULT_MODELS[LLM_BACKEND])
TOP_K = 5                      # chunks given to the LLM (5 x ~200 tokens fits easily in 4096)
REWRITE = os.environ.get("REWRITE", "1") == "1"      # rewrite the question into a fuller search query
FALLBACK = os.environ.get("FALLBACK", "1") == "1"    # labelled general-knowledge answer when the documents have nothing
NOT_FOUND = {
    "en": "I could not find this in the Erasmus+ Programme Guide or the IGU documents.",
    "tr": "Bunu Erasmus+ Program Rehberi'nde veya İGÜ belgelerinde bulamadım.",
}
LANGUAGE_NAMES = {"en": "English", "tr": "Turkish"}

SYSTEM_PROMPT = """You answer questions about the Erasmus+ programme for students of Istanbul Gelisim University (IGU).
Answer ONLY with information from the numbered passages below. Do not use your own knowledge.
Passages from "programme-guide-2027" are the EU rules for everyone; passages whose source starts with "igu-"
are IGU's own rules (exam, selection, grants). When both answer the question, give IGU's rule and say it is IGU's.
If the passages do not contain the answer, write "not found" and set "found" to false.
Keep the answer short (1-4 sentences) and keep exact numbers, amounts and dates as written.
Write the answer in the same language as the question (the passages are in English; translate what you use).
In "citations", list the numbers of the passages you used."""


JSON_INSTRUCTION = """
Reply with a JSON object with exactly these keys, in this order:
{"answer": "<short answer or 'not found'>", "citations": [<passage numbers>], "found": <true or false>}"""


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


def chat(system, user, schema=None):
    """One call to the configured LLM backend. With `schema`, the reply is JSON in that shape."""
    if LLM_BACKEND == "groq":
        return chat_groq(system, user, json_mode=schema is not None)
    return chat_ollama(system, user, schema)


def chat_ollama(system, user, schema=None):
    """Ollama's chat API; a JSON schema in `format` forces the reply into that shape."""
    body = {
        "model": LLM_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "stream": False,
        "options": {"temperature": 0, "num_ctx": 4096},
    }
    if schema:
        body["format"] = schema                    # structured output: the reply must match this schema
    response = requests.post(f"{OLLAMA_URL}/api/chat", json=body, timeout=300)
    response.raise_for_status()
    return response.json()["message"]["content"]


def groq_api_key():
    """The key comes from the GROQ_API_KEY environment variable or from .streamlit/secrets.toml
    (the same file Streamlit uses; it is in .gitignore, so the key is never committed)."""
    if os.environ.get("GROQ_API_KEY"):
        return os.environ["GROQ_API_KEY"].strip()
    secrets = Path(__file__).parent / ".streamlit" / "secrets.toml"
    with open(secrets, "rb") as f:
        return tomllib.load(f)["GROQ_API_KEY"].strip()


def chat_groq(system, user, json_mode=False, retries=5):
    """Groq's OpenAI-compatible API. The free tier allows about 8,000 tokens per minute,
    so on a 429 (rate limit) we wait and retry."""
    body = {
        "model": LLM_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    for attempt in range(retries):
        response = requests.post(GROQ_URL, headers={"Authorization": f"Bearer {groq_api_key()}"}, json=body, timeout=60)
        if response.status_code == 429 and attempt < retries - 1:
            time.sleep(10 * (attempt + 1))
            continue
        if not response.ok:            # Groq explains the problem in the body (e.g. an unknown model name)
            raise RuntimeError(f"Groq error {response.status_code}: {response.text}")
        return response.json()["choices"][0]["message"]["content"]


def ask_llm(prompt):
    """Ask for a cited answer from the passages, as structured JSON (LLMAnswer)."""
    system = SYSTEM_PROMPT + (JSON_INSTRUCTION if LLM_BACKEND == "groq" else "")
    return LLMAnswer.model_validate(json.loads(chat(system, prompt, schema=LLMAnswer.model_json_schema())))


REWRITE_PROMPT = """Rewrite the user's question about the Erasmus+ programme as one clear, complete search query
in English, as it would be phrased in the official Erasmus+ Programme Guide.
If the question is in another language (e.g. Turkish), translate it into English.
Keep every name, country and number from the question. Do not answer it.
Examples: "can i go to spain" -> "Is Spain an eligible destination country for an Erasmus+ mobility?"
"vize yardımı?" -> "What help do Erasmus+ participants get with their visa application?"
Reply with the query only."""


def rewrite_query(question):
    """Short questions ("can i go to italy") search badly; a fuller query finds the right pages."""
    query = chat(REWRITE_PROMPT, question).strip().strip('"').splitlines()[0][:300]
    return query if len(query) > 5 else question


FALLBACK_PROMPT = """The official Erasmus+ documents do not answer the user's question.
Give a short, helpful answer (2-3 sentences) from general knowledge about Erasmus+.
Do not invent amounts, dates or rules: for anything that depends on the university, the country or the year,
tell the student to check with their Erasmus office.
Write the answer in the same language as the question."""


def general_answer(question):
    """A clearly labelled answer from the model's own knowledge, used only when the documents have nothing."""
    return chat(FALLBACK_PROMPT, question).strip()


def answer(store, model, bm25, reranker, question, lang="en"):
    """Full RAG pipeline: rewrite -> retrieve -> rerank -> generate (-> labelled fallback).
    answer_type is "documents" (cited answer), "general" (labelled, not from the documents) or "none".
    `lang` is the language of the page ("en" or "tr"); the answer itself follows the language of the question."""
    search_query = rewrite_query(question) if REWRITE else question
    queries = [question] if search_query.lower() == question.lower() else [question, search_query]
    rows = retrieve(store, model, question, k=TOP_K, method="rerank", bm25=bm25, reranker=reranker, search_queries=queries)
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
    says_not_found = any(phrase in text.lower() for phrase in (
        "not found", "no answer", "do not cover", "not mentioned",           # English
        "bulunamadı", "bulamadım", "yer almıyor", "belirtilmemiş"))           # Turkish
    if says_not_found:                       # the flag and the text disagree: trust the text
        llm.found = False
    answer_type = "documents"
    if not llm.found:
        sources, text, answer_type = [], NOT_FOUND.get(lang, NOT_FOUND["en"]), "none"
        if FALLBACK:
            text, answer_type = general_answer(question), "general"

    return {
        "question": question,
        "found": llm.found,
        "answer_type": answer_type,
        "answer": text,
        "sources": sources,
        "search_query": search_query,
        "retrieved": [{"source": r[0], "page": r[1], "score": round(r[3], 3)} for r in rows],
    }


if __name__ == "__main__":
    import sys

    from sentence_transformers import CrossEncoder, SentenceTransformer

    from db import PgStore, connect
    from ingest import MODEL_NAME
    from retrieval import RERANKER_NAME, BM25Index

    question = " ".join(sys.argv[1:]) or "How much monthly grant does IGU pay for a traineeship in Italy?"
    store = PgStore(connect())
    result = answer(store, SentenceTransformer(MODEL_NAME, device="cpu"), BM25Index(store),
                    CrossEncoder(RERANKER_NAME, device="cpu"), question)
    print(json.dumps(result, indent=2, ensure_ascii=False))
