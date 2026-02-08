"""sift doctor — validate setup and index file."""

import math
import os
import sqlite3
import struct
import sys


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    msg = f"  [{status}] {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return condition


def run_doctor(index_path):
    print(f"sift doctor: checking {index_path}\n")
    all_pass = True

    # 1. File exists
    exists = os.path.isfile(index_path)
    all_pass &= check("Index file exists", exists, index_path)
    if not exists:
        print("\n  Index file not found. Run: sift index ./your-docs -o sift-index.db")
        sys.exit(1)

    # 2. Valid SQLite
    try:
        conn = sqlite3.connect(index_path)
        conn.execute("SELECT 1")
        all_pass &= check("Valid SQLite database", True)
    except Exception as e:
        all_pass &= check("Valid SQLite database", False, str(e))
        sys.exit(1)

    cur = conn.cursor()

    # 3. Required tables
    tables = {
        row[0]
        for row in cur.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view')"
        ).fetchall()
    }
    for t in ["chunks", "chunks_fts", "embeddings", "sift_metadata"]:
        all_pass &= check(f"Table '{t}' exists", t in tables)

    if not {"chunks", "embeddings", "sift_metadata"}.issubset(tables):
        print("\n  Missing required tables. Re-run: sift index ./your-docs")
        conn.close()
        sys.exit(1)

    # 4. Chunk count
    chunk_count = cur.execute("SELECT count(*) FROM chunks").fetchone()[0]
    all_pass &= check("Chunks indexed", chunk_count > 0, f"{chunk_count} chunks")

    # 5. Embedding count matches chunks
    emb_count = cur.execute("SELECT count(*) FROM embeddings").fetchone()[0]
    all_pass &= check(
        "Embedding count matches chunks",
        emb_count == chunk_count,
        f"{emb_count} embeddings, {chunk_count} chunks",
    )

    # 6. Embedding dimensions = 384
    blob = cur.execute("SELECT vector FROM embeddings LIMIT 1").fetchone()
    if blob:
        blob = blob[0]
        dim = len(blob) // 4
        all_pass &= check("Embedding dimensions", dim == 384, f"{dim}-dim")

        # 7. Vectors are L2-normalized
        vec = struct.unpack(f"{dim}f", blob)
        norm = math.sqrt(sum(v * v for v in vec))
        all_pass &= check(
            "Vectors L2-normalized", abs(norm - 1.0) < 0.01, f"norm={norm:.4f}"
        )
    else:
        all_pass &= check("Embedding data", False, "no embeddings found")

    # 8. Model metadata
    meta = dict(cur.execute("SELECT key, value FROM sift_metadata").fetchall())
    all_pass &= check("Model metadata", "model" in meta, meta.get("model", "missing"))
    all_pass &= check(
        "Model is MiniLM",
        "MiniLM" in meta.get("model", ""),
        meta.get("model", "unknown"),
    )

    # 9. FTS5 works
    try:
        fts_count = cur.execute(
            "SELECT count(*) FROM chunks_fts"
        ).fetchone()[0]
        all_pass &= check(
            "FTS5 index populated",
            fts_count == chunk_count,
            f"{fts_count} FTS entries",
        )
    except Exception as e:
        all_pass &= check("FTS5 index", False, str(e))

    # 10. File size
    size_kb = os.path.getsize(index_path) / 1024
    all_pass &= check("Index file size", size_kb > 10, f"{size_kb:.0f} KB")

    conn.close()

    print()
    if all_pass:
        print("All checks passed. Index is ready to serve.")
    else:
        print("Some checks failed. Fix the issues above and re-run sift doctor.")
        sys.exit(1)
