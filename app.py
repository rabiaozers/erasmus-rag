"""REST API and web page for the Erasmus+ assistant.

STORE=postgres (default): chunks in PostgreSQL + pgvector (local setup, docker compose)
STORE=memory:             chunks from demo/chunks.json + demo/embeddings.npy (public demo, no database)
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sentence_transformers import CrossEncoder, SentenceTransformer

from rag import LLM_MODEL, answer
from retrieval import EMBEDDING_MODEL, RERANKER_NAME, BM25Index

HERE = Path(__file__).parent
state = {}


def open_store():
    if os.environ.get("STORE", "postgres") == "memory":
        from memory_store import MemoryStore
        return MemoryStore(HERE / "demo" / "chunks.json", HERE / "demo" / "embeddings.npy")
    from db import PgStore, connect
    return PgStore(connect())


@asynccontextmanager
async def lifespan(app):
    """Load the models and the BM25 index once, when the server starts."""
    state["store"] = open_store()
    state["model"] = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
    state["reranker"] = CrossEncoder(RERANKER_NAME, device="cpu")
    state["bm25"] = BM25Index(state["store"])
    yield


app = FastAPI(title="Erasmus+ Assistant", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    lang: str = Field("en", pattern="^(en|tr)$")          # language of the page


class Source(BaseModel):
    source: str
    page: int


class Retrieved(Source):
    score: float


class AskResponse(BaseModel):
    question: str
    found: bool
    answer_type: str            # "documents" | "general" (labelled, not from the documents) | "none"
    answer: str
    sources: list[Source]
    search_query: str
    retrieved: list[Retrieved]


@app.get("/", include_in_schema=False)
def root():
    """The chat page (web/index.html); the API documentation stays at /docs."""
    return FileResponse(HERE / "web" / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "chunks": len(state["store"].all_chunks()), "llm": LLM_MODEL}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    try:
        return answer(state["store"], state["model"], state["bm25"], state["reranker"], request.question, request.lang)
    except Exception as error:          # e.g. Ollama is not running
        raise HTTPException(status_code=503, detail=f"Could not answer: {error}") from error
