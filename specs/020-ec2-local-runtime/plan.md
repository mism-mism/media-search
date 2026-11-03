# Plan: ec2-local-runtime

- Gemini transport: `_gemini_settings()` in `main.py` picks AI Studio (API key in a header) or Vertex + ADC; the annotator and the classifier share it. No change to request or response shape.
- CLI: `media_search.cli` is an HTTP client of the resident service (`MEDIA_SEARCH_API`), so one OpenCLIP model per box. `search` builds thumbnails and one self-contained page; `import` waits for the async job.
- Contracts: the HTTP API is unchanged; the CLI's JSON is a new contract consumed by mk2-harness's dispatcher (documented in `docs/run-ec2.md`).
- Infra (users, units, proxy, data) lives in mism-mism/mk2-harness, out of this repo.
