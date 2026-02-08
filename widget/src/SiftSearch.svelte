<svelte:options customElement="sift-search" />

<script>
  import { onMount, onDestroy } from "svelte";
  import { createDbWorker } from "sql.js-httpvfs";

  let { db = "/sift-index.db", theme = "light" } = $props();

  let query = $state("");
  let statusText = $state("Loading...");
  let results = $state([]);
  let resultTag = $state("lexical");
  let modelReady = $state(false);
  let ready = $state(false);

  const SQLJS_CDN = "https://cdn.jsdelivr.net/npm/sql.js-httpvfs@0.8.12/dist";

  let dbWorker = null;
  let embedWorker = null;
  let allVectors = null;
  let debounceTimer = null;

  // Fetch a script from CDN and return a same-origin blob URL
  async function blobUrlFromCDN(url) {
    const resp = await fetch(url);
    const code = await resp.text();
    const blob = new Blob([code], { type: "text/javascript" });
    return URL.createObjectURL(blob);
  }

  function createEmbedWorker() {
    const code = `
      let extractor = null;
      let cachedVectors = null;

      self.onmessage = async (e) => {
        const { type } = e.data;

        if (type === "init") {
          try {
            const { pipeline } = await import("https://cdn.jsdelivr.net/npm/@huggingface/transformers@3");
            extractor = await pipeline("feature-extraction", e.data.model || "Xenova/all-MiniLM-L6-v2", { dtype: "q8" });
            self.postMessage({ type: "ready" });
          } catch (err) {
            self.postMessage({ type: "error", error: err.message });
          }
        } else if (type === "cache-vectors") {
          cachedVectors = e.data.vectors.map((v) => ({
            chunkId: v.chunkId,
            vector: new Float32Array(v.vector),
          }));
          self.postMessage({ type: "vectors-cached", count: cachedVectors.length });
        } else if (type === "search") {
          if (!extractor) {
            self.postMessage({ type: "error", error: "Model not loaded yet" });
            return;
          }
          try {
            const output = await extractor(e.data.query, { pooling: "mean", normalize: true });
            const queryVec = output.tolist()[0];
            const scores = cachedVectors.map((item) => ({
              chunkId: item.chunkId,
              score: dotProduct(queryVec, item.vector),
            }));
            scores.sort((a, b) => b.score - a.score);
            self.postMessage({
              type: "semantic-results",
              results: scores.slice(0, e.data.limit || 10),
            });
          } catch (err) {
            self.postMessage({ type: "error", error: err.message });
          }
        }
      };

      function dotProduct(a, b) {
        let sum = 0;
        for (let i = 0; i < a.length; i++) sum += a[i] * b[i];
        return sum;
      }
    `;
    const blob = new Blob([code], { type: "text/javascript" });
    return new Worker(URL.createObjectURL(blob), { type: "module" });
  }

  onMount(async () => {
    try {
      statusText = "Loading search index...";
      const sqljsWorkerUrl = await blobUrlFromCDN(`${SQLJS_CDN}/sqlite.worker.js`);

      // Resolve db path to absolute URL — blob URL workers can't resolve relative paths
      const dbUrl = new URL(db, window.location.href).toString();

      dbWorker = await createDbWorker(
        [{ from: "inline", config: { serverMode: "full", url: dbUrl, requestChunkSize: 4096 } }],
        sqljsWorkerUrl,
        `${SQLJS_CDN}/sql-wasm.wasm`
      );

      statusText = "Loading vectors...";
      const vecRows = await dbWorker.db.query("SELECT chunk_id, vector FROM embeddings");
      allVectors = vecRows.map((row) => ({
        chunkId: row.chunk_id,
        vector: new Float32Array(
          row.vector.buffer ? row.vector.buffer : new Uint8Array(row.vector).buffer
        ),
      }));

      embedWorker = createEmbedWorker();
      embedWorker.onmessage = onWorkerMessage;

      const vectorsForWorker = allVectors.map((v) => ({
        chunkId: v.chunkId,
        vector: Array.from(v.vector),
      }));
      embedWorker.postMessage({ type: "cache-vectors", vectors: vectorsForWorker });
      embedWorker.postMessage({ type: "init" });

      statusText = "Ready for keyword search. Loading ML model...";
      ready = true;
    } catch (err) {
      statusText = `Error: ${err.message}`;
    }
  });

  onDestroy(() => {
    embedWorker?.terminate();
    clearTimeout(debounceTimer);
  });

  function onWorkerMessage(e) {
    if (e.data.type === "ready") {
      modelReady = true;
      statusText = "Semantic search ready.";
      if (query.trim()) doSearch(query.trim());
    } else if (e.data.type === "semantic-results") {
      showSemanticResults(e.data.results);
    } else if (e.data.type === "error") {
      statusText = `Model error: ${e.data.error}`;
    }
  }

  function onInput(e) {
    query = e.target.value;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      const q = query.trim();
      if (q.length > 1) {
        doSearch(q);
      } else {
        results = [];
      }
    }, 200);
  }

  async function doSearch(q) {
    try {
      const lexResults = await lexicalSearch(q);
      results = lexResults.map((r) => ({ ...r, tag: "keyword" }));
      resultTag = "lexical";
    } catch (err) {
      // FTS error — ignore
    }

    if (modelReady) {
      statusText = "Computing semantic search...";
      embedWorker.postMessage({ type: "search", query: q, limit: 10 });
    }
  }

  async function lexicalSearch(q) {
    const words = q.split(/\s+/).filter((w) => w.length > 1);
    if (!words.length) return [];
    const ftsQuery = words.map((w) => `"${w}"`).join(" OR ");
    const rows = await dbWorker.db.query(
      `SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ? LIMIT 10`,
      [ftsQuery]
    );
    if (!rows.length) return [];
    const ids = rows.map((r) => r.rowid);
    return getChunksByIds(ids);
  }

  async function getChunksByIds(ids) {
    if (!ids.length) return [];
    const placeholders = ids.map(() => "?").join(",");
    return dbWorker.db.query(
      `SELECT id, url, title, content FROM chunks WHERE id IN (${placeholders})`,
      ids
    );
  }

  async function showSemanticResults(ranked) {
    const ids = ranked.map((r) => r.chunkId);
    const chunks = await getChunksByIds(ids);
    const scoreMap = new Map(ranked.map((r) => [r.chunkId, r.score]));
    results = chunks
      .map((c) => ({ ...c, score: scoreMap.get(c.id) || 0, tag: "semantic" }))
      .sort((a, b) => b.score - a.score);
    resultTag = "semantic";
    statusText = "Semantic search ready.";
  }

  function snippet(text, max = 200) {
    return text.length > max ? text.slice(0, max) + "..." : text;
  }
</script>

<div class="sift" data-theme={theme}>
  <input
    type="text"
    class="sift-input"
    placeholder="Search..."
    value={query}
    oninput={onInput}
    disabled={!ready}
  />
  <div class="sift-status">{statusText}</div>
  {#if results.length > 0}
    <ul class="sift-results">
      {#each results as r}
        <li class="sift-result">
          <div class="sift-result-title">
            {r.title}
            <span class="sift-tag" class:sift-tag-semantic={r.tag === "semantic"} class:sift-tag-keyword={r.tag === "keyword"}>
              {r.tag}
            </span>
          </div>
          <div class="sift-result-url">{r.url}</div>
          <div class="sift-result-snippet">{snippet(r.content)}</div>
          {#if r.score !== undefined}
            <div class="sift-result-score">{r.score.toFixed(4)}</div>
          {/if}
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .sift {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    max-width: 640px;
    color: #1a1a1a;
  }
  .sift[data-theme="dark"] {
    color: #e0e0e0;
  }
  .sift-input {
    width: 100%;
    padding: 12px 16px;
    font-size: 1rem;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    outline: none;
    background: inherit;
    color: inherit;
    box-sizing: border-box;
  }
  .sift-input:focus {
    border-color: #4a9eff;
  }
  .sift[data-theme="dark"] .sift-input {
    border-color: #444;
  }
  .sift-status {
    font-size: 0.8rem;
    color: #999;
    margin-top: 8px;
    min-height: 1.2em;
  }
  .sift-results {
    margin-top: 16px;
    list-style: none;
    padding: 0;
  }
  .sift-result {
    padding: 12px 0;
    border-bottom: 1px solid #eee;
  }
  .sift[data-theme="dark"] .sift-result {
    border-bottom-color: #333;
  }
  .sift-result-title {
    font-weight: 600;
    font-size: 0.95rem;
    color: #1a73e8;
  }
  .sift[data-theme="dark"] .sift-result-title {
    color: #8ab4f8;
  }
  .sift-result-url {
    font-size: 0.75rem;
    color: #999;
    margin-top: 2px;
  }
  .sift-result-snippet {
    font-size: 0.85rem;
    color: #444;
    margin-top: 4px;
    line-height: 1.4;
  }
  .sift[data-theme="dark"] .sift-result-snippet {
    color: #aaa;
  }
  .sift-result-score {
    font-size: 0.7rem;
    color: #aaa;
    margin-top: 2px;
  }
  .sift-tag {
    display: inline-block;
    font-size: 0.65rem;
    font-weight: 400;
    padding: 1px 6px;
    border-radius: 3px;
    margin-left: 6px;
    vertical-align: middle;
  }
  .sift-tag-keyword {
    background: #e8f0fe;
    color: #4a9eff;
  }
  .sift-tag-semantic {
    background: #e6f4ea;
    color: #34a853;
  }
</style>
