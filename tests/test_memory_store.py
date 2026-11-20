import json

import numpy as np

from memory_store import MemoryStore


def test_vector_search_returns_most_similar_first(tmp_path):
    rows = [["doc", 1, "a"], ["doc", 2, "b"], ["doc", 3, "c"]]
    vectors = np.array([[1, 0], [0, 1], [0.6, 0.8]], dtype=np.float16)
    (tmp_path / "chunks.json").write_text(json.dumps(rows))
    np.save(tmp_path / "emb.npy", vectors)

    store = MemoryStore(tmp_path / "chunks.json", tmp_path / "emb.npy")
    results = store.vector_search(np.array([0, 1], dtype=np.float32), k=2)
    assert [r[1] for r in results] == [2, 3]
