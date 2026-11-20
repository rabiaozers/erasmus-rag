"""Free public demo on Streamlit Community Cloud.

The chat page (web/index.html) runs as a Streamlit component: the page sends the question to Python,
Python runs the same retrieval + LLM code as the API, and sends the answer back to the page.
Chunks are kept in memory (no PostgreSQL) and the LLM runs on Groq's free API.
"""
import os
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))                       # use rag.py, retrieval.py ... from the repository root

os.environ["LLM_BACKEND"] = "groq"                  # must be set before rag is imported
os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

from sentence_transformers import CrossEncoder, SentenceTransformer  # noqa: E402

from memory_store import MemoryStore  # noqa: E402
from rag import LLM_MODEL, answer  # noqa: E402
from retrieval import EMBEDDING_MODEL, RERANKER_NAME, BM25Index  # noqa: E402

st.set_page_config(page_title="erasmus.exe · Erasmus+ Assistant", page_icon="🌸", layout="wide")
st.markdown(                                        # let the chat page fill the whole Streamlit page
    """<style>
      header, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
      .stApp { background: #efe3ff; }
      .block-container, [data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: 100% !important; }
      [data-stale="true"] { opacity: 1 !important; }   /* no fading while Python is answering */
      iframe { display: block; }
    </style>""",
    unsafe_allow_html=True,
)

chat = components.declare_component("erasmus_chat", path=str(ROOT / "web"))


@st.cache_resource(show_spinner="Waking up the assistant (about a minute on the first visit)...")
def load():
    store = MemoryStore(ROOT / "demo" / "chunks.json", ROOT / "demo" / "embeddings.npy")
    return (store, SentenceTransformer(EMBEDDING_MODEL, device="cpu"), BM25Index(store),
            CrossEncoder(RERANKER_NAME, device="cpu"))


store, model, bm25, reranker = load()

request = chat(
    health={"chunks": len(store.all_chunks()), "llm": LLM_MODEL},
    result=st.session_state.get("result"),
    key="chat",
    default=None,
)

# A new question from the page: answer it once, then rerun so the page receives the result.
if request and request.get("id") != st.session_state.get("answered_id"):
    st.session_state["answered_id"] = request["id"]
    question = str(request.get("question", "")).strip()[:500]
    if len(question) < 3:
        result = {"error": "Please write a slightly longer question."}
    else:
        try:
            result = answer(store, model, bm25, reranker, question)
        except Exception as error:                  # e.g. the free LLM API is busy
            result = {"error": f"the assistant could not answer right now: {error}"[:300]}
    result["id"] = request["id"]
    st.session_state["result"] = result
    st.rerun()
