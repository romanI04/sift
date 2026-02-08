/**
 * SiftSearch — client-side semantic search engine.
 *
 * Loads a pre-built SQLite index via HTTP range requests,
 * provides instant FTS5 lexical results, then upgrades to
 * semantic results once the ML model loads in a WebWorker.
 */

import { createDbWorker } from "sql.js-httpvfs";

export class SiftSearch {
  constructor({ dbUrl, workerUrl, wasmUrl }) {
    this.dbUrl = dbUrl;
    this.workerUrl = workerUrl;
    this.wasmUrl = wasmUrl;
    this.db = null;
    this.embedWorker = null;
    this.modelReady = false;
    this.vectorsCached = false;
    this._chunks = new Map(); // id -> {url, title, content}
    this._pendingSearches = [];
  }

  async init(embedWorkerUrl) {
    // 1. Initialize sql.js-httpvfs
    this.db = await createDbWorker(
      [
        {
          from: "inline",
          config: {
            serverMode: "full",
            url: this.dbUrl,
            requestChunkSize: 4096,
          },
        },
      ],
      this.workerUrl,
      this.wasmUrl
    );

    // 2. Start embed worker
    this.embedWorker = new Worker(embedWorkerUrl, { type: "module" });
    this.embedWorker.onmessage = (e) => this._onWorkerMessage(e);

    // 3. Preload all vectors and send to embed worker
    await this._preloadVectors();

    // 4. Start model loading (non-blocking)
    this.embedWorker.postMessage({ type: "init" });
  }

  async _preloadVectors() {
    const rows = await this.db.db.query(
      "SELECT chunk_id, vector FROM embeddings"
    );
    const vectors = rows.map((row) => ({
      chunkId: row.chunk_id,
      vector: Array.from(new Float32Array(row.vector.buffer)),
    }));

    this.embedWorker.postMessage({ type: "cache-vectors", vectors });
  }

  _onWorkerMessage(e) {
    const { type } = e.data;

    if (type === "ready") {
      this.modelReady = true;
      // Process any pending semantic searches
      for (const pending of this._pendingSearches) {
        this.embedWorker.postMessage(pending.msg);
        pending.resolve();
      }
      this._pendingSearches = [];
    } else if (type === "vectors-cached") {
      this.vectorsCached = true;
    } else if (type === "semantic-results") {
      if (this._semanticCallback) {
        this._resolveSemantic(e.data.results);
      }
    } else if (type === "error") {
      console.error("Embed worker error:", e.data.error);
      if (this._rejectSemantic) {
        this._rejectSemantic(new Error(e.data.error));
      }
    }
  }

  /**
   * Search for a query. Returns results via callbacks.
   *
   * @param {string} query - Search query
   * @param {object} options
   * @param {function} options.onLexical - Called with FTS5 results immediately
   * @param {function} options.onSemantic - Called with semantic results when ready
   * @param {number} options.limit - Max results (default 10)
   */
  async search(query, { onLexical, onSemantic, limit = 10 } = {}) {
    // 1. Instant FTS5 lexical search
    if (onLexical) {
      try {
        const lexResults = await this._lexicalSearch(query, limit);
        onLexical(lexResults);
      } catch (err) {
        console.error("FTS5 search error:", err);
        onLexical([]);
      }
    }

    // 2. Semantic search (waits for model if not ready)
    if (onSemantic) {
      try {
        const semResults = await this._semanticSearch(query, limit);
        onSemantic(semResults);
      } catch (err) {
        console.error("Semantic search error:", err);
        onSemantic([]);
      }
    }
  }

  async _lexicalSearch(query, limit) {
    // FTS5 MATCH query — no ORDER BY rank (per architecture decision)
    const ftsQuery = query
      .split(/\s+/)
      .filter((w) => w.length > 1)
      .map((w) => `"${w}"`)
      .join(" OR ");

    if (!ftsQuery) return [];

    const rows = await this.db.db.query(
      `SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ? LIMIT ?`,
      [ftsQuery, limit]
    );

    if (!rows.length) return [];

    const ids = rows.map((r) => r.rowid);
    return this._getChunksByIds(ids);
  }

  async _semanticSearch(query, limit) {
    return new Promise((resolve, reject) => {
      this._resolveSemantic = async (ranked) => {
        const ids = ranked.map((r) => r.chunkId);
        const chunks = await this._getChunksByIds(ids);
        // Attach scores
        const scoreMap = new Map(ranked.map((r) => [r.chunkId, r.score]));
        for (const chunk of chunks) {
          chunk.score = scoreMap.get(chunk.id) || 0;
        }
        chunks.sort((a, b) => b.score - a.score);
        resolve(chunks);
      };
      this._rejectSemantic = reject;

      const msg = { type: "search", query, limit };

      if (this.modelReady) {
        this.embedWorker.postMessage(msg);
      } else {
        // Queue until model is ready
        this._pendingSearches.push({
          msg,
          resolve: () => this.embedWorker.postMessage(msg),
        });
      }
    });
  }

  async _getChunksByIds(ids) {
    if (!ids.length) return [];

    const placeholders = ids.map(() => "?").join(",");
    const rows = await this.db.db.query(
      `SELECT id, url, title, content FROM chunks WHERE id IN (${placeholders})`,
      ids
    );

    return rows.map((r) => ({
      id: r.id,
      url: r.url,
      title: r.title,
      content: r.content,
    }));
  }
}
