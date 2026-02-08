# Sift vs Keyword Search on FastAPI Docs

We indexed FastAPI's entire documentation (146 pages, 2,123 chunks) and ran the same queries through both.

## Results

| What the user searches | Sift returns | Keyword search returns |
|----------------------|-------------|----------------------|
| "how to protect my API from unauthorized access" | Security First Steps, OAuth2 with JWT, Scopes | Alternatives page, comparisons, test metadata |
| "handling file uploads from users" | Request Files, Request Forms and Files, UploadFile | Test metadata, alternatives |
| "running background jobs" | Background Tasks, BackgroundTasks reference | Starlette comparison, async docs |
| "how to test my endpoints" | Testing WebSockets, Testing Dependencies, Testing guide | Test metadata (4x) |

## Why this happens

FastAPI's docs say "Request Files." Users search "file uploads."
FastAPI's docs say "Background Tasks." Users search "background jobs."
FastAPI's docs say "Security First Steps." Users search "protect my API."

Keyword search needs exact word matches. Sift understands that these mean the same thing.

## Try it yourself

**[Interactive side-by-side comparison →](https://astonishing-creponne-e1d3d8.netlify.app/compare.html)**

```bash
pip install sift-search
sift index ./docs -o sift-index.db
```
