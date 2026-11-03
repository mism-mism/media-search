---
reviewer_role: test-reviewer
reviewer_id: independent-test-review-020
---

# Test review

FAIL

Independent read-only evaluation of `git diff 13335f5` (commits `de6f1f4`,
`77949b2` plus the uncommitted `pytest.importorskip("requests")` in
`tests/test_gemini_annotator.py`) against AC1–AC4. No implementation changes.

Suite in the CI-equivalent venv (no `requests`):
`pytest -q -p no:cacheprovider` → 186 passed, 2 skipped, 1 warning — matches
`verification.md`.

To check whether the new tests actually fail when the code breaks, I applied
single-line mutations to a scratch copy of `src/` (not the worktree) and ran
`tests/test_cli_020.py tests/test_gemini_annotator.py tests/test_annotation_runtime.py`
in the same venv:

| Mutation | Result |
|----------|--------|
| API key appended to the URL as `?key=` | caught |
| Classifier built without `_gemini_settings()` | caught |
| `image.thumbnail(...)` removed (no 512 px cap) | caught |
| `asset_id` not escaped in HTML | caught |
| Busy check `409` changed | caught |
| Poll loop stops on `running` | caught |
| Exception message instead of type name printed | caught |
| `x-goog-api-key` header line removed | **survives** (header test skipped in CI) |
| `EXIT_BUSY = 75` changed to `1` | **survives** |
| `status != "succeeded"` check removed (failed job reported as success) | **survives** |
| Tags not escaped in HTML | **survives** |
| `HTTPError → ApiError` mapping in `http_fetch` removed | survives (non-blocking) |
| `MEDIA_SEARCH_API` default changed | survives (non-blocking) |
| Final catch-all `except Exception` removed | survives (non-blocking) |

## AC1 — Gemini via API key

Covered: AI Studio URL, key absent from URL and from the raised
`ImageAnnotationError` (`__cause__ is None`), runtime wiring without
`GOOGLE_CLOUD_PROJECT` for both annotator and classifier, Vertex path still
green through the existing tests.

Blocking gap: the only test that the key travels in `x-goog-api-key`
(`test_api_key_session_sends_the_key_as_a_header`) is skipped in CI because
`requests` is not in `dev`; the other API-key test monkeypatches
`_api_key_session` away. In CI nothing fails if the header is never set, which
is the central AC1 transport claim. Either install the `gemini-key` extra in the
CI/dev environment, or inject a fake `requests` module (`sys.modules`) so the
header assertion always runs.

Non-blocking: no test for "neither `GEMINI_API_KEY` nor `GOOGLE_CLOUD_PROJECT`"
raising the new message, nor for the key taking precedence when both are set.
The classifier's own error path with an API key is not exercised, but it uses
the same `from None` pattern. Without the extra, every annotation silently
becomes `generation_failed` (documented in `docs/run-ec2.md`, not tested or
surfaced at startup).

## AC2 — `search`

Covered end to end through the real app (fake embedder, local adapters):
JSON shape, JPEG thumbnail ≤ 512 px from a 1600×900 source, one page with two
data URIs, no `<script`, query/display name/asset id escaped, one line per hit
without `--json`, empty query rejected.

Blocking gap: tags are always empty in the fixture (annotation off), so tag
escaping is untested — and tags are model output, the most likely untrusted
text on the page. Add one hit with a tag like `<b>x</b>` (e.g. via
`render_html` directly).

Non-blocking: `http_fetch` (`MEDIA_SEARCH_API`, `HTTPError → ApiError`, a
connection error) has no unit test; the EC2 smoke in `verification.md` covers a
real call once. The "CLI loads no model" constraint is not asserted (e.g. that
importing `media_search.cli` pulls in no embedder module). The video
representative-frame thumbnail is untested, consistent with video import being
out of scope. Empty query exits 2, which AC2/AC3 do not specify.

## AC3 — `import`

Covered: real import through `POST /api/import` returns the same three lists;
async polling (`queued → running → succeeded`) with URL-quoted job id; 409 →
`{error: "import_busy"}`; HTTP and unexpected failures print only a short code.

Blocking gaps:
- The busy test asserts `code == cli.EXIT_BUSY`, not `75`; changing the constant
  passes. Pin the literal the AC and the dispatcher depend on.
- A job ending in `failed` (e.g. lock lost inside the worker, or Gemini/IO
  errors) is untested: removing the `succeeded` check makes the CLI print empty
  lists and exit 0, i.e. report failure as success. Add a `failed` reply that
  expects exit 1 and `{error: "import_failed"}`.

Non-blocking: timeout path untested; busy is simulated with a fake 409 rather
than a held `fs` lock (the real app does map `ImportLockBusy` to 409 in
`api/app.py`); a non-409 error on the initial POST is untested.

## AC4 — docs and gates

`docs/run-ec2.md` lists `MEDIA_BACKEND=local`, `FRAME_BACKEND=local`,
`IMPORT_LOCK_BACKEND=fs`, leaving out `MEDIA_SEARCH_DB_GCS`, `GEMINI_API_KEY`
in `media.env`, and both CLI calls with exit 75. It does not mention
`MEDIA_SEARCH_API` or that the CLI requires the resident service (default
`http://127.0.0.1:3200`); worth one line.

"Unit tests cover AC1–AC3" is not met while the four surviving mutations above
remain. `git diff --check 13335f5` reports trailing whitespace in
`specs/020-ec2-local-runtime/checklist.md` lines 3–4 (Markdown hard breaks;
fix or confirm the gate ignores them). The `importorskip` fix is uncommitted;
commit it before gates. Lifecycle gates and the independent Outer review were
not run by this reviewer.

## Required to PASS

1. Make the `x-goog-api-key` header assertion run in CI.
2. Assert exit code `75` literally.
3. Test a `failed` import job → exit 1, `{error: "import_failed"}`.
4. Test that tags are HTML-escaped.

This verdict is the test evaluator result only, not feature or merge completion.
