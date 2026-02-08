import os
import sqlite3
import tempfile
from sift_search.indexer import build_index


def test_index_and_query():
    with tempfile.TemporaryDirectory() as d:
        # write test docs
        for name, body in [
            ("auth.md", "# Authentication\n\nUse JWT tokens to authenticate API requests. Every endpoint requires a valid bearer token in the Authorization header.\n"),
            ("deploy.md", "# Deployment\n\nDeploy your application to any cloud provider. We support AWS, GCP, and Azure out of the box.\n"),
        ]:
            with open(os.path.join(d, name), "w") as f:
                f.write(body)

        db_path = os.path.join(d, "test.db")
        build_index(d, db_path)

        assert os.path.exists(db_path)

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # chunks exist
        cur.execute("SELECT COUNT(*) FROM chunks")
        assert cur.fetchone()[0] >= 2

        # FTS5 works
        cur.execute("SELECT title FROM chunks_fts WHERE chunks_fts MATCH 'authentication' LIMIT 5")
        rows = cur.fetchall()
        assert any("Authentication" in r[0] for r in rows)

        # embeddings exist and are correct size
        cur.execute("SELECT LENGTH(vector) FROM embeddings LIMIT 1")
        vec_bytes = cur.fetchone()[0]
        assert vec_bytes == 384 * 4  # float32

        conn.close()
