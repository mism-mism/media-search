---
reviewer_role: security-reviewer
reviewer_id: independent-annotation-security-review
---

PASS

Independent Outer security evaluation of the current 016 changes against HEAD
`b69866c` on 2026-09-06. Read the Constitution, security rules, reviewer contract,
spec, clarify and plan. Unrelated `.playwright-mcp/` and
`014-folder-nav-deep.png` were excluded. No application code, tests or cloud
resources were modified by this reviewer.

Evidence:

- `GeminiImageAnnotator` obtains ADC in its infrastructure adapter and sends
  authenticated HTTPS requests only to the constructed Google AI Platform
  hostname. Configuration rejects path/URL injection characters. Requests
  disable redirects and credential-refresh retries, use a 45-second transport
  timeout, and expose no arbitrary URL or tool-execution interface.
- Input exceeding 30 MiB or 40 million pixels is rejected by the adapter.
  Accepted images are re-encoded as RGB JPEG with maximum dimensions 1024 by
  1024 before transmission. The prompt treats image text as data, prohibits
  identity/SKU/sensitive-attribute guesses, and requests descriptive fields only.
- Requests cap generated output at 2048 tokens. Responses require a completed
  candidate, bounded generated text, exact JSON keys and string types; the
  domain value enforces 1–12 tags of at most 40 characters and a nonempty
  description of at most 300 characters. Generated content cannot set product
  identity, manual metadata, paths, credentials or executable instructions.
- All adapter failures are reduced to `ImageAnnotationError("generation_failed")`
  without provider bodies or credential details. The application persists only
  fixed failure/deferred codes. Concurrent imports reserve their per-run budget
  under a lock before each attempt; failure consumes an attempt and there is no
  immediate automatic generation retry. The existing single-writer import
  boundary remains in place.
- Generated description and each generated tag pass through the existing `esc`
  function before interpolation into card HTML. SQLite writes and added search
  predicates bind their data as parameters. No new shell, SQL or path sink takes
  generated text. Additive API fields expose annotation values/status, not raw
  provider errors.
- Terraform adds an optional custom role containing only
  `aiplatform.endpoints.predict`, bound to the existing runtime service account;
  it does not add model administration, IAM administration, storage privileges
  or public invokers. Make/Actions carry matching service and Import Job settings.
  Existing IAP/IAM configuration and Make's `--no-allow-unauthenticated` remain
  intact. No new endpoint bypasses the established IAP boundary.
- Operator documentation records the Google Cloud transfer, global-location
  limitation, explicit enable/disable settings, minimal IAM prerequisite,
  bounded reimport and distinction between a per-import limit and a spending
  limit. The sample artifact contains generated descriptions and retrieval
  outcomes, with no credentials; its accompanying note explicitly distinguishes
  local-user authentication from production Import Job authentication.

Observed verification: `.venv/bin/python -m pytest -q
tests/test_gemini_annotator.py tests/test_image_annotations.py
tests/test_annotation_import.py` passed **46 tests**. This includes rejection of
invalid/refused provider output, safe timeout/403/429 errors with one request,
fixed endpoint/disabled redirect assertions, concurrent budget enforcement and
execution of the HTML rendering function with hostile generated strings.
Complete output is retained at
`/private/tmp/016-security-review-logs/logs/2026-09-06/6e4e7612-c4d1-4613-8eeb-495f1057f46c/`.

No blocking security finding in the reviewed change. Limits: the adapter checks
byte size after receiving bytes from the importer, and the response text limit
is checked after the trusted Google response is decoded; these are not claims
of whole-process memory or absolute wall-clock bounds. Automated secret and
dependency vulnerability gates remain `SKIP(not_configured)` per repository
rules, not PASS. Production IAM application, deployed IAP verification and a
real Import Job call remain release verification responsibilities; this review
does not assert those cloud actions have happened or authorize additional scope.
