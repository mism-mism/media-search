---
reviewer_role: code-quality-reviewer
reviewer_id: independent-quality-review-020
---

Verdict: PASS

Reviewed `git diff 13335f5` (including the uncommitted change to
`tests/test_gemini_annotator.py`) against the active 020 spec and
`rules/code-quality.md` in a separate evaluator invocation. Scope: local
correctness and maintainability of `src/media_search/cli.py`,
`src/media_search/adapters/gemini_annotator.py`, `_gemini_settings` in
`src/media_search/main.py`, the `gemini-key` extra in `pyproject.toml`,
`docs/run-ec2.md` and the new/changed tests. No implementation edits were made.

| Axis | Evidence |
|------|----------|
| Correctness | Key handling: `_api_key_session` puts the key only in the `x-goog-api-key` session header; the AI Studio URL is built from the validated model name alone (`gemini_annotator.py:47`). `annotate` and `GeminiCategoryClassifier.classify` keep re-raising fixed codes `from None`, so neither the key, a provider body nor a `requests` exception message reaches job errors; `tests/test_gemini_annotator.py` asserts the key is absent from the URL, the error repr and `__cause__`. `_gemini_settings` raises a message that names env vars, never values. The Vertex path keeps its project/location validation (an empty default `project` is still rejected). CLI escaping: `render_html` passes every text field (query, display name, tags, asset id) through `html.escape` (quote-safe for the `alt` attribute); the only unescaped values are base64, an int index and a formatted float. Failure paths: 409 on `POST /api/import` maps to `BusyError` → exit 75 `{error: "import_busy"}`; other errors print only an own short code or an exception class name, never `str(exc)` of foreign exceptions, so `URLError` hosts and provider text stay off stdout. Job polling has a deadline and URL-quotes the job id. |
| Understandability | `cli.py` reads top to bottom: transport (`http_fetch`), presentation (`thumbnail`, `render_html`), two use-case functions (`search`, `import_media`), then `main`. The module docstring states the non-obvious why (one OpenCLIP model per box, dispatcher never reads the media folder). `_gemini_settings` makes the API-key-vs-Vertex choice explicit in one place, and its docstring says so. Comments are WHY comments (`EX_TEMPFAIL`, first request may warm the model, key never in URL). |
| Changeability | Annotator and classifier now share one settings function instead of two hand-copied constructor calls, removing the earlier `os.environ["GOOGLE_CLOUD_PROJECT"]` KeyError trap in `build_runtime`. Both transports keep the same request/response code, so tag continuity (spec requirement) is structural rather than duplicated. `main(argv, fetch=...)` and `search(fetch, ...)`/`import_media(fetch, ...)` take the transport as a parameter, which is what lets `tests/test_cli_020.py` run the real app through `TestClient` without a network. |
| Simplicity | Stdlib `argparse` and `urllib` for the CLI, already-present Pillow for thumbnails, `requests` only in an extra (it was already in `gcp`). No new abstraction, wrapper class or fallback beyond what the spec asks; the two tiny exception types carry real control flow (busy vs. other). |

## Non-blocking follow-ups (recommended)

1. Missing `gemini-key` extra fails late and silently. `import requests` runs
   lazily inside the session factory, and `annotate`/`classify` convert every
   exception to `generation_failed`/`classification_failed`. If the box is
   installed without `.[gemini-key]` (or `.[gcp]`), the service starts, imports
   succeed, and every image just records an annotation failure. `docs/run-ec2.md`
   does not name the extra. Suggest either naming `pip install ".[gemini-key]"`
   in the doc or importing `requests` in `_gemini_settings` (startup) when the
   key path is chosen.
2. One undecodable thumbnail fails the whole search. `search` calls `thumbnail()`
   for every hit with no per-hit guard; a video without `best_frame_key` falls
   back to `/media/<video>` in `thumbnail_url_for`, which Pillow cannot open, so
   the CLI exits 1 for the whole query. Video import is out of scope on EC2 and
   current data is images only, so this is latent. Relatedly, the
   `if h["thumbnail"]` filter in `render_html` is dead (the value is never empty),
   which suggests a tolerance that was intended but not implemented; either drop
   the filter or return `thumbnail: null` for a failed hit and keep it.
3. Error mapping in `main` is string-typed: `str(exc).startswith(("http_",
   "import_"))` and `str(exc) == "empty_query"`. It is correct today and the
   safety property (no foreign message printed) holds, but a dedicated
   exception (or letting argparse reject an empty query) would be easier to
   change than prefix sniffing.

Verification: `git diff --check 13335f5` reports only two trailing double-space
hard line breaks in `specs/020-ec2-local-runtime/checklist.md` (intentional
Markdown, not code). Reviewed `verification.md` (186 passed, 2 skipped in the
CI-equivalent env; targeted 24 passed; EC2 CLI smoke run); the suite was not
re-run in this review. No mechanical lint/type result is claimed
(`NOT_CONFIGURED`).

N/A: inheritance, domain error translation across layers (no domain code
changed; architecture scope belongs to the architecture reviewer).

Required follow-ups: none blocking.
