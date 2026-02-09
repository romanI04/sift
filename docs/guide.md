# Add Sift to Your Static Site

Sift adds semantic search to any static site. Visitors search by meaning, not just keywords. No server required.

## 1. Install the CLI

```bash
pip install sift-search
```

## 2. Index your content

Point sift at your markdown docs:

```bash
sift index ./docs -o sift-index.db
```

This reads your `.md` files, computes embeddings, and outputs a single `sift-index.db` file.

Verify it worked:

```bash
sift doctor sift-index.db
```

## 3. Add the widget

Copy `sift-index.db` to your site's public directory (where static assets are served from).

Add this to your HTML:

```html
<script type="module" src="https://cdn.jsdelivr.net/npm/sift-search@latest/dist/sift-search.js"></script>

<sift-search db="/sift-index.db"></sift-search>
```

That's it. Your visitors now have semantic search.

## How it works

- **Build time:** The CLI reads your markdown, splits it into chunks, and computes embeddings using all-MiniLM-L6-v2 (a small, fast language model). Everything is stored in a SQLite database.
- **Runtime:** The browser loads the database via HTTP range requests when available, or downloads the full index as fallback. Keyword search works instantly via FTS5. Once the ML model loads in the visitor's browser, results upgrade to semantic.
- **No server:** The index is a static file. The model runs client-side. Works on Netlify, Vercel, GitHub Pages, Cloudflare Pages, or any static host.

## Requirements

- **Your site:** Any static host that serves files with correct `Content-Length` headers and supports range requests (all major hosts do).
- **Headers needed:** Your host must serve the `.db` file without compressing it (compression breaks range requests). Add these headers for `.db` files:
  - `Cache-Control: public, max-age=3600, no-transform`
  - `Content-Encoding: identity`
  - `Accept-Ranges: bytes`
- **Browsers:** Chrome, Edge, Firefox (latest), Safari 16+.
- **COOP/COEP (optional):** These headers enable HTTP range requests (partial index download). Without them, sift downloads the full index file instead — still works, just a larger initial load.
  - `Cross-Origin-Opener-Policy: same-origin`
  - `Cross-Origin-Embedder-Policy: credentialless`

### Netlify example

Add to `netlify.toml` at your repo root:

```toml
[[headers]]
  for = "/*"
  [headers.values]
    Cross-Origin-Opener-Policy = "same-origin"
    Cross-Origin-Embedder-Policy = "credentialless"

[[headers]]
  for = "/*.db"
  [headers.values]
    Accept-Ranges = "bytes"
    Cache-Control = "public, max-age=3600, no-transform"
    Content-Type = "application/octet-stream"
    Content-Encoding = "identity"
```

## Attributes

| Attribute | Default | Description |
|-----------|---------|-------------|
| `db` | `/sift-index.db` | Path to your index file |
| `theme` | `light` | `light` or `dark` |

## Updating the index

Re-run `sift index` whenever your content changes. Add it to your build script:

```json
{
  "scripts": {
    "build": "sift index ./docs -o public/sift-index.db && your-build-command"
  }
}
```

## Troubleshooting

Run `sift doctor sift-index.db` to check your index. It validates:
- SQLite structure and required tables
- Embedding dimensions (384) and L2 normalization
- FTS5 full-text index population
- Model metadata
