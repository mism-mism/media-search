---
reviewer_role: test-reviewer
reviewer_id: independent-test-review-020
---

# Test review

PASS

Independent read-only evaluation of `git diff 13335f5...HEAD` at `5ce3ac6`
(feature/ec2-local, clean working tree) against AC1–AC4. No implementation
changes. This re-review replaces the FAIL at `77949b2`; its four blocking gaps
are closed (see table).

Suite in the CI-equivalent venv (no `requests`):
`pytest -q -p no:cacheprovider` → 190 passed, 1 skipped (optional real OpenCLIP),
1 warning. The header test no longer skips. `git diff --check 13335f5` → clean.

To check that the tests actually fail when the code breaks, I applied single-line
mutations to a scratch copy of `src/` (not the worktree) and ran
`tests/test_cli_020.py tests/test_gemini_annotator.py tests/test_annotation_runtime.py`
in the same venv. Baseline with no mutation: 27 passed.

| Mutation | Result |
|----------|--------|
| `x-goog-api-key` header line removed | caught (was surviving) |
| Key sent under another header name | caught |
| API key appended to the URL as `?key=` | caught |
| Classifier built without `_gemini_settings()` | caught |
| `EXIT_BUSY = 75` changed to `1` | caught (was surviving) |
| Busy check `409` changed | caught |
| `status != "succeeded"` check removed | caught (was surviving) |
| Poll loop stops on `running` | caught |
| Tags not escaped in HTML | caught (was surviving) |
| `asset_id` not escaped in HTML | caught |
| `image.thumbnail(...)` removed (no 512 px cap) | caught |
| Exception message printed instead of type name | caught |
| `MEDIA_SEARCH_API` ignored | caught |
| `HTTPError → ApiError` mapping removed | caught |
| Per-hit thumbnail guard removed | caught |
| Blank-thumbnail skip in HTML removed | caught |
| Final catch-all `except Exception` removed | survives (non-blocking) |

## AC1 — Gemini via API key

Covered: AI Studio URL; key only in `x-goog-api-key` (the header test now stubs
`requests` via `sys.modules`, so it runs in CI); key absent from the URL and from
the raised `ImageAnnotationError` (`__cause__ is None`); runtime builds both the
annotator and the classifier from the key without `GOOGLE_CLOUD_PROJECT`; the
Vertex path is still green through the existing tests.

Non-blocking: the stub proves the header is set on whatever `requests.Session`
returns, not that real `requests` sends it (verified once in a local venv with
`requests`, per `verification.md`). No test for neither variable set, or for the
key winning when both are set. Without the `gemini-key` extra every annotation
becomes `generation_failed`; this is documented, not detected at startup.

## AC2 — `search`

Covered end to end through the real app: JSON shape, JPEG ≤ 512 px from a
1600×900 source, one self-contained page with data URIs and no `<script`, query,
name, id and generated tags escaped (an `onerror` payload in an annotation tag),
one line per hit without `--json`, empty query rejected. `http_fetch` is now
tested for the `MEDIA_SEARCH_API` base (trailing slash trimmed) and
`HTTPError → ApiError`.

New behavior in `5ce3ac6`, tested but not in AC2: an unreadable thumbnail yields
`thumbnail: ""` and the hit is left out of the HTML grid, while the heading still
counts it. The guard catches every exception, so a resident service that fails
all thumbnail requests (e.g. 503) still returns exit 0 with blank thumbnails.
Reasonable for the dispatcher, but consider stating it in AC2 or the docs so the
consumer handles `""`. "CLI loads no model" is not asserted by a test; the module
imports only stdlib and PIL. The video representative frame is untested,
consistent with video import being out of scope.

## AC3 — `import`

Covered: real import through `POST /api/import` returns the same three lists;
async polling with a URL-quoted job id; 409 → exit `75` (asserted literally) and
`{error: "import_busy"}`; a `failed` job → exit 1 and `{error: "import_failed"}`
without the job's error text; HTTP and unexpected errors print only a short code.

Non-blocking: timeout path untested; busy is a fake 409, not a held `fs` lock
(the real app maps `ImportLockBusy` to 409 in `api/app.py`); removing the final
catch-all is not caught, because no test raises an exception type outside the
named handlers (e.g. `URLError` when the service is down).

## AC4 — docs and gates

`docs/run-ec2.md` lists `MEDIA_BACKEND=local`, `FRAME_BACKEND=local`,
`IMPORT_LOCK_BACKEND=fs`, leaving out `MEDIA_SEARCH_DB_GCS`, `GEMINI_API_KEY` in
`media.env`, the `gemini-key` extra, `MEDIA_SEARCH_API` and the resident service,
and both CLI calls with exit 75. Unit tests now cover AC1–AC3 with the mutation
evidence above. The checklist trailing-whitespace issue is fixed.

This verdict is the test evaluator result only. Lifecycle gates, the independent
Outer review and CI on the pushed commit were not run by this reviewer and remain
the implementer's responsibility.
