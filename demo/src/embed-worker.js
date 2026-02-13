/**
 * WebWorker: handles query embedding (Transformers.js) and cosine similarity.
 * All heavy ML compute happens here, never on the main thread.
 */

import { pipeline } from "@huggingface/transformers";

let extractor = null;
let cachedVectors = null; // [{chunkId, vector: Float32Array}]

self.onmessage = async (e) => {
  const { type } = e.data;

  if (type === "init") {
    try {
      extractor = await pipeline(
        "feature-extraction",
        "Xenova/bge-small-en-v1.5",
        { dtype: "q8" }
      );
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
      const output = await extractor(e.data.query, {
        pooling: "mean",
        normalize: true,
      });
      const queryVec = output.tolist()[0];

      // Cosine similarity (vectors are L2-normalized, so dot product = cosine)
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
  for (let i = 0; i < a.length; i++) {
    sum += a[i] * b[i];
  }
  return sum;
}
