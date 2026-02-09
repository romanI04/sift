# sift

[![CI](https://github.com/romanI04/sift/actions/workflows/ci.yml/badge.svg)](https://github.com/romanI04/sift/actions)
[![PyPI](https://img.shields.io/pypi/v/sift-search.svg)](https://pypi.org/project/sift-search/)
[![npm](https://img.shields.io/npm/v/sift-search.svg)](https://www.npmjs.com/package/sift-search)
[![license](https://img.shields.io/github/license/romanI04/sift.svg)](https://github.com/romanI04/sift)

Semantic search for static sites. Two commands to install, zero servers to run.

![sift vs keyword search](https://siftsearch.netlify.app/sift-comparison.png)

## Usage

Install the CLI and index your docs:

```bash
pip install sift-search
sift index ./docs -o public/sift-index.db
```

Add the widget to your site:

```html
<script type="module" src="https://cdn.jsdelivr.net/npm/sift-search@latest/dist/sift-search.js"></script>
<sift-search db="/sift-index.db"></sift-search>
```

Visitors get semantic search. No backend. No API keys. No monthly bill.

## How it works

**Build time:** `sift index` reads your markdown, splits into chunks, and computes embeddings with [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) (ONNX). Output is a single SQLite file.

**Runtime:** The browser loads the SQLite file via [HTTP range requests](https://github.com/phiresky/sql.js-httpvfs) — no full download needed. Keyword results appear instantly via FTS5. Once the ML model loads client-side (~2s), results upgrade to semantic.

**No server.** The index is a static file. The model runs in the browser via [Transformers.js](https://huggingface.co/docs/transformers.js). Deploy on Netlify, Vercel, GitHub Pages, Cloudflare Pages, or any static host.

## Why

Keyword search needs exact matches. Users don't think in exact matches.

Search "how to protect my API" on FastAPI's docs — keyword search returns the Alternatives page. Sift returns Security First Steps, OAuth2, and JWT.

**[See it yourself](https://siftsearch.netlify.app/compare.html)** — side-by-side on FastAPI's full docs (146 pages, 2,123 chunks).

## Details

`sift doctor` validates your index (14 checks). Dark mode with `<sift-search theme="dark">`. 92KB JS bundle (gzip 27KB), plus on-demand WASM and model loading. Supports Chrome, Edge, Firefox (latest), Safari 16+.

Your static host must serve `.db` files without compression (breaks range requests). See the [installation guide](docs/guide.md) for header config.

## Credits

Built on [sql.js-httpvfs](https://github.com/phiresky/sql.js-httpvfs) by phiresky, [Transformers.js](https://github.com/huggingface/transformers.js) by Hugging Face, and [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2).

## License

MIT
