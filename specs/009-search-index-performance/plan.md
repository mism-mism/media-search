# Plan: Search + index performance

## Search

1. `make deploy` / Terraform: `--min-instances=1` (service).
2. Eager-load OpenCLIP in `main.py` lifespan / startup (call `embed_text("warmup")`).
3. Wrap embedder with process-local LRU for text (and optional image hash).
4. `MetadataRepositoryPort.search_text(needle)` → sqlite
   `display_name LIKE` / tags_json LIKE (case-insensitive); in-memory adapter
   mirrors behavior.
5. `SearchMediaAssets` uses that instead of `list_all` for text merge.

## Index

1. ImportDirectory: worker pool for embed (thread pool), queue results to
   single thread/lock for vector+metadata upserts (reuse db lock).
2. Raise Cloud Run Job CPU/memory (e.g. 4 CPU / 16Gi) in Makefile + terraform.
3. Keep differential skip by `size_bytes`.

## Evidence

`docs/research/009-search-index-performance.md` — baseline method + after
numbers (local hermetic timings OK for unit; prod sample when available).
