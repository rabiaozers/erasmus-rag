"""PostgreSQL + pgvector: create the table, store chunks, search them."""
import os

import psycopg
from pgvector.psycopg import register_vector

DB_URL = os.environ.get("DB_URL", "postgresql://rag:rag@localhost:5433/rag")

SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    page INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(384)
);
"""


def connect():
    """Open a connection and make sure the table exists."""
    conn = psycopg.connect(DB_URL, autocommit=True)
    conn.execute(SCHEMA)
    register_vector(conn)          # lets us pass numpy arrays as vectors
    return conn


def reset(conn):
    """Empty the table before a new experiment (avoids duplicate chunks)."""
    conn.execute("TRUNCATE chunks RESTART IDENTITY;")


def insert_chunks(conn, chunks, embeddings, source):
    """Store each chunk with its page number and embedding."""
    with conn.cursor() as cur:
        for chunk, emb in zip(chunks, embeddings):
            cur.execute(
                "INSERT INTO chunks (source, page, content, embedding) VALUES (%s, %s, %s, %s)",
                (source, chunk["page"], chunk["text"], emb),
            )


def search(conn, query_embedding, k=5):
    """Return the k most similar chunks as (source, page, content, similarity)."""
    rows = conn.execute(
        """
        SELECT
            source,
            page,
            content,
            1 - (embedding <=> %s::vector) AS similarity
        FROM chunks
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
        """,
        (query_embedding, query_embedding, k),
    ).fetchall()
    return rows


def keyword_search(conn, question, k=20):
    """Full-text search: chunks that share words with the question, best first."""
    rows = conn.execute(
        """
        WITH q AS (SELECT replace(plainto_tsquery('english', %s)::text, '&', '|')::tsquery AS query)
        SELECT source, page, content,
               ts_rank(to_tsvector('english', content), q.query) AS rank
        FROM chunks, q
        WHERE to_tsvector('english', content) @@ q.query
        ORDER BY rank DESC
        LIMIT %s;
        """,
        (question, k),
    ).fetchall()
    return rows


def all_chunks(conn):
    """Every chunk as (source, page, content), in id order. Used to build the BM25 index."""
    return conn.execute("SELECT source, page, content FROM chunks ORDER BY id;").fetchall()


class PgStore:
    """Chunks stored in PostgreSQL (local setup). Same interface as MemoryStore in memory_store.py."""

    def __init__(self, conn):
        self.conn = conn

    def vector_search(self, query_embedding, k):
        return search(self.conn, query_embedding, k)

    def keyword_search(self, question, k):
        return keyword_search(self.conn, question, k)

    def all_chunks(self):
        return all_chunks(self.conn)
