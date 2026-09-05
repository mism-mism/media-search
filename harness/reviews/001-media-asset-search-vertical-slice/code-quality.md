---
reviewer_role: code-quality-reviewer
reviewer_id: code-quality-review-subagent
---

# Code quality review — 001-media-asset-search-vertical-slice

**Verdict: PASS**

Scope: local maintainability of `src/media_search/` and `tests/` against
`rules/code-quality.md` (Correctness / Understandability / Changeability /
Simplicity). Architecture/dependency-direction findings are out of scope
except where they affect local readability or error locality.

Mechanical enforcers (format/lint/type/complexity/dead-code): N/A —
`NOT_CONFIGURED` in rules; judgment review only.

---

## Correctness — PASS

| Evidence | Assessment |
|----------|------------|
| `domain/frames.py` encodes R9–R10 (`SHORT_VIDEO_THRESHOLD_SECONDS`, uniform ends) with rejection of negative duration | Spec rules are explicit and test-backed (`tests/test_representative_frames.py`) |
| `EmptyQueryError` → HTTP 400 in `api/app.py`; empty/whitespace `q` rejected in `SearchMediaAssets` | Failure path is explicit; covered by unit + API tests |
| Import: unsupported → `ImportWarning` + continue; per-file `except` records reason and attempts orphan vector cleanup | Primary failures are not swallowed; cleanup bare-`except` is secondary and intentional (`import_directory.py`) |
| Path traversal guards on `/media/` and `/thumbnails/` via `relative_to` | Boundary failures translated at the HTTP edge |
| Vector dim mismatch raises `ValueError` in `SqliteVecSearch.upsert_frame` | No silent coerce |
| Collapse-to-max-frame score + tags AND in `search_media.py` | Matches R11/R14; unit tests assert behavior |

Non-blocking: nested cleanup `except Exception: pass` after a failed import can hide secondary cleanup errors — acceptable for batch continue semantics, but a debug log would make the path clearer later.

---

## Understandability — PASS

| Evidence | Assessment |
|----------|------------|
| Names follow domain language (`MediaAsset`, `ImportDirectory`, `SearchMediaAssets`, `FrameHit`, `classify_path`) | No `utils` / `helpers` / `manager` / `misc` |
| Package layout: `domain` / `ports` / `application` / `adapters` / `api` | One clear responsibility per module at this slice size |
| WHY comments where needed (EOF seek margin in `media_probe.py`, FastAPI thread + lock in `sqlite_store.py` / `main.py`, Fake vs semantic AC on embedders) | Comments do not merely restate WHAT |
| `FakeEmbedder` vs `OpenClipEmbedder` roles are stated in docstrings | Intent is readable for wiring vs semantic gates |

Non-blocking nits:

- `application/search_media.py` imports unused `MediaAsset` and `MediaType`.
- `ImportDirectory._index_frames(..., asset)` lacks a type annotation (elsewhere typed).
- `VectorSearchPort.search` returns opaque `(asset_id, frame_key, score, position)` tuples — workable at 001 scale; a small named type would reduce reader load.
- Some tests reach into `InMemoryVectorSearch._frames` (`test_video_import.py`) — acceptable for slice size, slightly couples tests to storage shape.

---

## Changeability — PASS

| Evidence | Assessment |
|----------|------------|
| Ports (`EmbeddingPort`, `VectorSearchPort`, `MetadataRepositoryPort`) + in-memory and SQLite adapters | Swap seams without rewriting use cases |
| `EMBEDDER=fake|local` in `main.py`; DI via `create_app(...)` | Config and tests inject fakes cleanly |
| Use cases own orchestration; adapters own I/O (ffprobe/ffmpeg, sqlite-vec, OpenCLIP) | Single clear reason to change per unit |
| No speculative multi-backend framework or generic plugin registry | Avoids premature generalization |

Non-blocking nit: `_MAX_FRAME_SLOTS = 3` in `import_directory.py` duplicates `MAX_REPRESENTATIVE_FRAMES` instead of importing it — drift risk if the constant changes.

---

## Simplicity — PASS

| Evidence | Assessment |
|----------|------------|
| No inheritance hierarchies; composition of ports into use cases | Matches “composition over unnecessary inheritance” |
| Inline minimal HTML UI in `api/app.py` | Appropriate for a vertical slice; not a parallel SPA framework |
| `plan_video_frames` is a thin adapter over domain `representative_frame_positions` | Not speculative indirection |
| Duplicate cosine-normalize in memory vs sqlite adapters | Same *shape*, different stores — not abstracted prematurely (rules: do not abstract mere similarity) |
| No placeholder stubs or error suppression to green tests | AI anti-patterns not observed |

---

## Required follow-ups

None (PASS). Optional nits above may be cleaned opportunistically; they do not fail any axis.

## Summary

The slice is cohesive, named in domain terms, failure-explicit at import/search/API boundaries, and free of speculative AI abstractions. Axes hold; nits are non-blocking.
