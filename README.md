# sift

[![CI](https://github.com/romanI04/sift/actions/workflows/ci.yml/badge.svg)](https://github.com/romanI04/sift/actions)
[![PyPI](https://img.shields.io/pypi/v/sift-search.svg)](https://pypi.org/project/sift-search/)
[![npm](https://img.shields.io/npm/v/sift-search.svg)](https://www.npmjs.com/package/sift-search)
[![license](https://img.shields.io/github/license/romanI04/sift.svg)](https://github.com/romanI04/sift)

Semantic search for static sites. Two commands to install, zero servers to run.

![sift vs keyword search](https://siftsearch.netlify.app/sift-comparison.png)

## Quick start

```bash
pip install sift-search
sift index ./docs -o public/sift-index.db
```

```html
<script type="module" src="https://cdn.jsdelivr.net/npm/sift-search@latest/dist/sift-search.js"></script>
<sift-search db="/sift-index.db"></sift-search>
```

Visitors get semantic search. No backend. No API keys. No monthly bill.

## How it works

**Build time:** `sift index` reads your content, splits into chunks, and computes embeddings with [bge-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5) (ONNX, quantized). Output is a single SQLite file.

**Runtime:** The browser loads the SQLite index via [HTTP range requests](https://github.com/phiresky/sql.js-httpvfs) — no full download needed. Keyword results appear instantly via FTS5. Once the ML model loads client-side, results upgrade to semantic.

**No server.** The index is a static file. The model runs in the visitor's browser via [Transformers.js](https://huggingface.co/docs/transformers.js). Deploy on Netlify, Vercel, GitHub Pages, Cloudflare Pages — anywhere you serve files.

## Two modes

**Local mode** (default) — everything runs in the browser. Zero API calls. The embedding model (34MB, quantized) loads in a WebWorker. Best for privacy-sensitive sites and offline-capable docs.

**Cloud mode** — bring your own embedding endpoint. Set the `api` attribute and queries are embedded server-side. No model download, instant semantic search from the first keystroke. Cosine similarity still runs client-side against your static index.

```html
<!-- local mode (default) -->
<sift-search db="/sift-index.db"></sift-search>

<!-- cloud mode -->
<sift-search db="/sift-index.db" api="https://your-endpoint.com/embed"></sift-search>
```

## Why

Keyword search needs exact matches. Users don't think in exact matches.

Search "how to protect my API" — keyword search returns the Alternatives page. Sift returns Security First Steps, OAuth2, and JWT.

**[Try it yourself](https://siftsearch.netlify.app/compare.html)** — side-by-side on FastAPI's full docs (146 pages, 2,123 chunks).

## CLI options

```bash
# Index with local ONNX model (default, free)
sift index ./docs -o sift-index.db

# Index with OpenAI embeddings (faster for large sites)
pip install sift-search[openai]
OPENAI_API_KEY=sk-... sift index ./docs -o sift-index.db --provider openai

# Validate your index
sift doctor sift-index.db
```

## Details

- **Model:** bge-small-en-v1.5 — 384 dimensions, quantized to 34MB ONNX. Same model runs in Python (onnxruntime) and browser (Transformers.js).
- **Index:** SQLite with FTS5 for keyword search + vector blobs for semantic search. Served via HTTP range requests.
- **Widget:** 94KB JS bundle (28KB gzip). Dark mode: `<sift-search theme="dark">`.
- **Validation:** `sift doctor` runs 14 checks on your index (schema, dimensions, normalization, FTS5, metadata).
- **Browsers:** Chrome, Edge, Firefox (latest), Safari 16+.
- **Hosts:** Works best with COOP/COEP headers for range requests. Without them, falls back to full index download. See [installation guide](docs/guide.md).

## Sift vs alternatives

| | Sift | Pagefind | Orama | Algolia |
|---|---|---|---|---|
| Semantic search | Yes | No (keyword only) | Yes (cloud only) | Yes (cloud only) |
| No server required | Yes | Yes | No | No |
| Free to run | Yes | Yes | Free tier, then $499/mo | $50+/mo |
| Client-side ML | Yes (local mode) | N/A | No | No |
| Privacy-first option | Yes | Yes | No | No |
| Index format | SQLite (range requests) | Binary index | Cloud | Cloud |

## Credits

Built on [sql.js-httpvfs](https://github.com/phiresky/sql.js-httpvfs) by phiresky, [Transformers.js](https://github.com/huggingface/transformers.js) by Hugging Face, and [bge-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5) by BAAI.

## License

MIT
