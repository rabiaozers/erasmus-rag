"""Build the demo index (demo/chunks.json + demo/embeddings.npy) straight from the documents in data/.

Same chunks and embeddings as ingest.py + export_index.py, but without PostgreSQL:
useful when you only want to update the public demo after adding a document.

    python build_index.py
"""
import json
import time

import numpy as np
from sentence_transformers import SentenceTransformer

from chunking import SOURCES, load_source, split_pages
from retrieval import EMBEDDING_MODEL

if __name__ == "__main__":
    start = time.time()
    model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")

    rows, vectors = [], []
    for source, path in SOURCES:
        chunks = [c for c in split_pages(load_source(path)) if c["text"].strip()]   # skip empty chunks
        texts = [c["text"] for c in chunks]
        vectors.append(model.encode(texts, convert_to_numpy=True, normalize_embeddings=True))
        rows += [[source, c["page"], c["text"]] for c in chunks]
        print(f"{source}: {len(chunks)} chunks")

    with open("demo/chunks.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    embeddings = np.vstack(vectors).astype(np.float16)                              # float16 halves the size
    np.save("demo/embeddings.npy", embeddings)
    print("saved", len(rows), "chunks", embeddings.shape, f"in {time.time() - start:.0f} s")
