"""Read every source document, embed every chunk and store it in PostgreSQL."""
import time

from sentence_transformers import SentenceTransformer

from chunking import SOURCES, load_source, split_pages
from db import connect, insert_chunks, reset

MODEL_NAME = "all-MiniLM-L6-v2"


if __name__ == "__main__":
    start = time.time()

    model = SentenceTransformer(MODEL_NAME, device="cpu")   # the GPU is busy with the LLM
    conn = connect()
    reset(conn)

    for source, path in SOURCES:
        chunks = split_pages(load_source(path))
        chunks = [c for c in chunks if c["text"].strip()]      # skip empty chunks
        texts = [c["text"] for c in chunks]
        embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True)
        insert_chunks(conn, chunks, embeddings, source=source)
        print(f"{source}: {len(chunks)} chunks")

    print("stored:", conn.execute("SELECT count(*) FROM chunks").fetchone()[0])
    print(f"done in {time.time() - start:.0f} s")
