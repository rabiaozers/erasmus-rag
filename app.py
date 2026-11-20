"""REST API for the Erasmus+ assistant."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sentence_transformers import CrossEncoder, SentenceTransformer

from db import connect
from ingest import MODEL_NAME
from rag import answer
from retrieval import RERANKER_NAME, BM25Index

state = {}


@asynccontextmanager
async def lifespan(app):
    """Load the models and the BM25 index once, when the server starts."""
    state["conn"] = connect()
    state["model"] = SentenceTransformer(MODEL_NAME, device="cpu")
    state["reranker"] = CrossEncoder(RERANKER_NAME, device="cpu")
    state["bm25"] = BM25Index(state["conn"])
    yield
    state["conn"].close()


app = FastAPI(title="Erasmus+ Assistant", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class Source(BaseModel):
    source: str
    page: int


class Retrieved(Source):
    score: float


class AskResponse(BaseModel):
    question: str
    found: bool
    answer: str
    sources: list[Source]
    retrieved: list[Retrieved]


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")


@app.get("/health")
def health():
    chunks = state["conn"].execute("SELECT count(*) FROM chunks").fetchone()[0]
    return {"status": "ok", "chunks": chunks}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    try:
        return answer(state["conn"], state["model"], state["bm25"], state["reranker"], request.question)
    except Exception as error:          # e.g. Ollama is not running
        raise HTTPException(status_code=503, detail=f"Could not answer: {error}") from error
