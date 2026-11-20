"""Copy the chunks and embeddings from PostgreSQL into two files for the public demo (no database there)."""
import json

import numpy as np

from db import connect

if __name__ == "__main__":
    conn = connect()
    rows = conn.execute("SELECT source, page, content, embedding FROM chunks ORDER BY id;").fetchall()
    with open("demo/chunks.json", "w", encoding="utf-8") as f:
        json.dump([[source, page, content] for source, page, content, _ in rows], f, ensure_ascii=False)
    embeddings = np.array([row[3].to_numpy() for row in rows], dtype=np.float16)   # pgvector returns Vector objects; float16 halves the size
    np.save("demo/embeddings.npy", embeddings)
    print("exported", len(rows), "chunks", embeddings.shape)
