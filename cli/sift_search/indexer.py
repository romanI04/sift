"""Build sift-index.db from a directory of markdown files."""

import sqlite3
import struct

from .chunker import chunk_directory
from .embedder import EMBEDDING_DIM, Embedder


def vector_to_blob(vec):
    """Pack a float32 numpy array into a bytes blob."""
    return struct.pack(f"{len(vec)}f", *vec)


def build_index(content_dir, output_path="sift-index.db"):
    """Build the SQLite index from markdown content.

    1. Chunk all .md files in content_dir
    2. Compute embeddings via ONNX
    3. Write SQLite with chunks, FTS5, and embeddings
    """
    print(f"Scanning {content_dir} for markdown files...")
    chunks = chunk_directory(content_dir)
    if not chunks:
        print("No chunks found. Check that the directory contains .md files.")
        return

    print(f"Found {len(chunks)} chunks. Computing embeddings...")
    embedder = Embedder()
    texts = [c["content"] for c in chunks]
    vectors = embedder.embed(texts)

    print(f"Writing index to {output_path}...")
    conn = sqlite3.connect(output_path)
    cur = conn.cursor()

    # Schema
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            title, content, content=chunks, content_rowid=id
        );

        CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
            INSERT INTO chunks_fts(rowid, title, content)
            VALUES (new.id, new.title, new.content);
        END;

        CREATE TABLE IF NOT EXISTS embeddings (
            chunk_id INTEGER PRIMARY KEY REFERENCES chunks(id),
            vector BLOB NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sift_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """
    )

    # Insert chunks (triggers populate FTS5 automatically)
    for i, chunk in enumerate(chunks):
        cur.execute(
            "INSERT INTO chunks (id, url, title, content) VALUES (?, ?, ?, ?)",
            (i + 1, chunk["url"], chunk["title"], chunk["content"]),
        )

    # Insert embeddings
    for i, vec in enumerate(vectors):
        cur.execute(
            "INSERT INTO embeddings (chunk_id, vector) VALUES (?, ?)",
            (i + 1, vector_to_blob(vec)),
        )

    # Store metadata
    cur.execute(
        "INSERT INTO sift_metadata (key, value) VALUES (?, ?)",
        ("model", embedder.model_name),
    )
    cur.execute(
        "INSERT INTO sift_metadata (key, value) VALUES (?, ?)",
        ("embedding_dim", str(EMBEDDING_DIM)),
    )

    conn.commit()
    conn.close()

    print(f"Done. {len(chunks)} chunks indexed → {output_path}")
