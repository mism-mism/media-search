---
reviewer_role: code-quality-reviewer
reviewer_id: independent-annotation-quality-review
---

# Code quality review: 016-image-auto-tags

Verdict: PASS

Reviewed the feature's uncommitted implementation, tests, configuration and documentation against HEAD `b69866c`, `spec.md`, `clarify.md`, `plan.md`, and `rules/code-quality.md`. This is an independent Inner evaluator invocation; the reviewer did not modify implementation or tests. Unrelated `.playwright-mcp/` and `014-folder-nav-deep.png` were excluded.

## Evidence

- **Correctness:** `application/import_directory.py` reserves the per-import annotation budget under a lock and confines writes to the existing single-writer path. `frames=None` explicitly represents annotation-only work, preventing vector/thumbnail deletion. Existing successful annotations are reused for unchanged images, including when missing vectors need rebuilding; changed images discard stale generated metadata. Provider failures become persisted `generation_failed` and cap exhaustion becomes `limit_reached` while indexing remains usable.
- **Understandability:** `domain/media_asset.py` keeps generated tags, description and provenance together in `ImageAnnotation`, distinct from manual metadata. `search_tags` and `annotation_status` name their domain purpose directly. `api/app.py` uses a small shared response base for the additive annotation fields and a focused card renderer with escaped generated strings.
- **Changeability:** `ports/annotation.py` exposes one operation and a safe boundary exception. `adapters/gemini_annotator.py` contains endpoint construction, credentials, image preparation, request construction and response parsing; tests inject the transport without real credentials. `main.py` performs optional adapter selection. The change does not introduce a generic provider framework or unnecessary abstraction.
- **Simplicity and persistence:** `adapters/sqlite_store.py` uses two additive columns and a shared migration helper for initial and replaced connections. Generated JSON is queried by descriptive fields, so provenance/JSON serialization do not become accidental keywords. Memory and SQL tests exercise matching behavior and combined manual/generated tag filters.
- **Failure clarity:** The Gemini adapter bounds dimensions, encoded input and generated text; non-success responses and invalid/refused output become a single safe port error with no provider body. The import use case recognizes that error explicitly. Existing best-effort cleanup behavior is retained; no new silent provider failure path or speculative fallback was introduced.
- **Configuration:** Make, workflow and Terraform configure both service and Import Job. Runtime defaults to disabled enrichment, and documentation explains the explicit production setting, prerequisites, retries, limits and bounded backfill. Reference-category classification remains excluded.

## Observed verification

Reviewer ran `.venv/bin/python -m pytest tests/test_annotation_import.py tests/test_gemini_annotator.py tests/test_image_annotations.py tests/test_annotation_runtime.py -q`: **49 passed**, with two dependency deprecation warnings, in 0.73 seconds. The suite includes import/retry/budget behavior, provider boundaries, SQLite reload/migration, GET/POST keyword retrieval, composition and generated-text escaping.

Raw execution evidence: `/private/tmp/media-search-016-quality-logs/logs/2026-09-06/734f0311-64cc-4635-a7cf-73bddc68958d`.

No blocking local maintainability or correctness findings. No required follow-ups. Architecture/security judgment, production release verification and feature-wide gate convergence remain with their assigned evaluators and the main agent; this PASS does not claim those checks were run by this reviewer. Formatting, lint, type-safety, complexity and dead-code enforcers are marked `NOT_CONFIGURED` in the repository rules and are not claimed as mechanical PASS.
