import { createDbWorker } from "sql.js-httpvfs";

const workerUrl = new URL(
  "sql.js-httpvfs/dist/sqlite.worker.js",
  import.meta.url
).toString();
const wasmUrl = new URL(
  "sql.js-httpvfs/dist/sql-wasm.wasm",
  import.meta.url
).toString();

const input = document.getElementById("search-input");
const status = document.getElementById("status");
const resultsList = document.getElementById("results");

let db = null;
let embedWorker = null;
let modelReady = false;
let allVectors = null; // [{chunkId, vector: Float32Array}]

async function init() {
  try {
    // 1. Load SQLite via HTTP range requests
    status.textContent = "Loading search index...";
    db = await createDbWorker(
      [
        {
          from: "inline",
          config: {
            serverMode: "full",
            url: "/sift-index.db",
            requestChunkSize: 4096,
          },
        },
      ],
      workerUrl,
      wasmUrl
    );

    // 2. Preload vectors
    status.textContent = "Loading vectors...";
    const vecRows = await db.db.query(
      "SELECT chunk_id, vector FROM embeddings"
    );
    allVectors = vecRows.map((row) => ({
      chunkId: row.chunk_id,
      vector: new Float32Array(
        row.vector.buffer
          ? row.vector.buffer
          : new Uint8Array(row.vector).buffer
      ),
    }));

    // 3. Start embed worker
    embedWorker = new Worker(new URL("./embed-worker.js", import.meta.url), {
      type: "module",
    });
    embedWorker.onmessage = onWorkerMessage;

    // Send vectors to worker
    const vectorsForWorker = allVectors.map((v) => ({
      chunkId: v.chunkId,
      vector: Array.from(v.vector),
    }));
    embedWorker.postMessage({ type: "cache-vectors", vectors: vectorsForWorker });

    // Start model loading
    status.textContent = "Ready for keyword search. Loading ML model...";
    embedWorker.postMessage({ type: "init" });

    input.disabled = false;
  } catch (err) {
    status.textContent = `Error: ${err.message}`;
    console.error(err);
  }
}

function onWorkerMessage(e) {
  if (e.data.type === "ready") {
    modelReady = true;
    status.textContent = "Semantic search ready.";
    // If there's a query in the input, re-run it with semantic
    if (input.value.trim()) {
      doSearch(input.value.trim());
    }
  } else if (e.data.type === "semantic-results") {
    showSemanticResults(e.data.results);
  } else if (e.data.type === "error") {
    console.error("Worker error:", e.data.error);
    status.textContent = `Model error: ${e.data.error}`;
  }
}

let debounceTimer = null;
input.addEventListener("input", () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    const query = input.value.trim();
    if (query.length > 1) {
      doSearch(query);
    } else {
      resultsList.innerHTML = "";
    }
  }, 200);
});

async function doSearch(query) {
  // 1. Instant FTS5 lexical search
  try {
    const lexResults = await lexicalSearch(query);
    renderResults(lexResults, "lexical");
  } catch (err) {
    console.error("FTS error:", err);
  }

  // 2. Semantic search if model ready
  if (modelReady) {
    status.textContent = "Computing semantic search...";
    embedWorker.postMessage({ type: "search", query, limit: 10 });
  }
}

async function lexicalSearch(query) {
  const words = query.split(/\s+/).filter((w) => w.length > 1);
  if (!words.length) return [];

  const ftsQuery = words.map((w) => `"${w}"`).join(" OR ");

  const rows = await db.db.query(
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
  const rows = await db.db.query(
    `SELECT id, url, title, content FROM chunks WHERE id IN (${placeholders})`,
    ids
  );
  return rows;
}

async function showSemanticResults(ranked) {
  const ids = ranked.map((r) => r.chunkId);
  const chunks = await getChunksByIds(ids);

  // Attach scores and sort
  const scoreMap = new Map(ranked.map((r) => [r.chunkId, r.score]));
  const results = chunks.map((c) => ({
    ...c,
    score: scoreMap.get(c.id) || 0,
  }));
  results.sort((a, b) => b.score - a.score);

  renderResults(results, "semantic");
  status.textContent = "Semantic search ready.";
}

function renderResults(results, tag) {
  resultsList.innerHTML = "";
  if (!results.length) {
    resultsList.innerHTML = '<li class="result">No results found.</li>';
    return;
  }

  for (const r of results) {
    const li = document.createElement("li");
    li.className = "result";

    const snippet =
      r.content.length > 200 ? r.content.slice(0, 200) + "..." : r.content;
    const tagClass = tag === "semantic" ? "tag-semantic" : "tag-lexical";
    const tagLabel = tag === "semantic" ? "semantic" : "keyword";
    const scoreHtml =
      r.score !== undefined
        ? `<div class="result-score">score: ${r.score.toFixed(4)}</div>`
        : "";

    li.innerHTML = `
      <div class="result-title">${escapeHtml(r.title)}<span class="result-tag ${tagClass}">${tagLabel}</span></div>
      <div class="result-url">${escapeHtml(r.url)}</div>
      <div class="result-snippet">${escapeHtml(snippet)}</div>
      ${scoreHtml}
    `;
    resultsList.appendChild(li);
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

init();
