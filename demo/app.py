"""Public demo on Streamlit Community Cloud: same retrieval code, chunks kept in memory, LLM through Groq."""
import os
import sys
from pathlib import Path

import streamlit as st

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))               # use retrieval.py, rag.py ... from the repository root

os.environ["LLM_BACKEND"] = "groq"                 # must be set before rag is imported
os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

from sentence_transformers import CrossEncoder, SentenceTransformer  # noqa: E402

from memory_store import MemoryStore  # noqa: E402
from rag import LLM_MODEL, answer  # noqa: E402
from retrieval import RERANKER_NAME, BM25Index  # noqa: E402

EMBEDDING_MODEL = "all-MiniLM-L6-v2"               # the same model that embedded the chunks
SOURCE_NAMES = {
    "programme-guide-2027": ("Erasmus+ Programme Guide 2027", "page"),
    "igu-steps": ("IGU step-by-step traineeship guide", "page"),
    "igu-slides": ("IGU orientation slides", "slide"),
}
EXAMPLES = [
    "How much monthly grant does IGU pay for a traineeship in Italy?",
    "How long can a Youth Exchange last?",
    "Which documents do I need after returning to receive the final 20% of the grant?",
    "Is there extra money for travel by train instead of plane?",
    "Can I have a relationship during Erasmus?",
]


@st.cache_resource(show_spinner="Loading the search models (about a minute on the first visit)...")
def load():
    store = MemoryStore(HERE / "chunks.json", HERE / "embeddings.npy")
    return (store, SentenceTransformer(EMBEDDING_MODEL, device="cpu"), BM25Index(store),
            CrossEncoder(RERANKER_NAME, device="cpu"))


def cite(source, page):
    name, unit = SOURCE_NAMES.get(source, (source, "page"))
    return f"{name}, {unit} {page}"


st.set_page_config(page_title="Erasmus+ Assistant", page_icon="🇪🇺")
st.title("Erasmus+ Assistant")
st.write(
    "Answers questions about the Erasmus+ programme from the 466-page EU Programme Guide 2027 and "
    "Istanbul Gelişim University's traineeship documents, **with the pages it used**. "
    "Hybrid search (embeddings + BM25), a reranker, and an LLM that must say when the documents do not cover a question. "
    "[Code, evaluation and results on GitHub](https://github.com/rabiaozers/erasmus-rag)"
)

store, model, bm25, reranker = load()

example = st.selectbox("Try an example", ["(type your own)"] + EXAMPLES)
question = st.text_input("Your question (in English)", value="" if example == "(type your own)" else example)

if st.button("Ask", type="primary") and question.strip():
    with st.spinner("Searching the documents and writing the answer..."):
        try:
            result = answer(store, model, bm25, reranker, question.strip())
        except Exception as error:
            st.error(f"Could not answer right now ({error}). The free LLM API may be busy; try again in a minute.")
            st.stop()

    if result["found"]:
        st.success(result["answer"])
        st.markdown("**Sources:** " + "; ".join(cite(s["source"], s["page"]) for s in result["sources"]))
    else:
        st.info(result["answer"])

    with st.expander("What the search retrieved (top 5 after reranking)"):
        for r in result["retrieved"]:
            st.write(f"- {cite(r['source'], r['page'])} (reranker score {r['score']})")

st.caption(
    f"LLM: {LLM_MODEL} via Groq. Not official advice: always check with your Erasmus office. "
    "The IGU documents belong to Istanbul Gelişim University's International Exchange and Cooperation Office."
)
