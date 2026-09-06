---
reviewer_role: product-reviewer
reviewer_id: independent-annotation-product-review
---

PASS

Independent Outer product review of feature 016 against baseline `b69866c`,
performed 2026-09-06. Reviewed spec, clarification decisions, plan, tasks,
implementation, test evidence, operator documentation and the recorded live
sample. Unrelated `.playwright-mcp/` and `014-folder-nav-deep.png` were excluded.
The reviewer changed only this artifact and made no provider requests.

## Acceptance and product evidence

- **AC1:** `tests/test_image_annotations.py::test_import_to_persisted_api_keyword_search`
  covers import, SQLite reopen, GET search for a generated tag and POST search
  for a generated description word absent from the name/manual fields. Library,
  search and detail responses expose separate generated metadata; detail includes
  model/prompt provenance. The independent test reviewer observed the suite pass.
- **AC2:** Import preserves manual fields and exact product identity. Successful
  unchanged annotations are reused; missing/failed annotations enter the
  annotation-only path with `frames=None`, preserving frame vectors/thumbnails.
  Rebuilding missing vectors can reuse successful generation. The Inner review
  and import tests cover preservation, reuse and retry.
- **AC3:** The locked per-import reservation caps attempts, including failures,
  before calling the provider. Safe provider errors persist `failed`; budget
  exhaustion persists `deferred`. Both can be retried on later import without
  deleting existing frames. New-image generation failure still saves prepared
  vectors. Card messages expose failure/retry or deferred state; generated text
  never replaces the user's metadata. Boundary and concurrent-cap tests cover
  the required failure cases.
- **AC4:** SQLite migration initializes generated fields empty for old rows and
  runs for opened/replaced connections. SQL and memory search inspect manual and
  generated descriptions/tags; filtering uses their combined tag set. Provenance
  and JSON serialization are excluded from keywords. Existing text-match priority,
  exact product filters and semantic/image candidates remain in the search use case.
- **AC5:** The Gemini adapter uses authenticated Google model endpoints, bounded
  JPEG input, output schema/length checks, a timeout, disabled redirects and safe
  errors. `annotationHtml` escapes tags and description and labels expandable
  content `AIタグ・説明` / `AIによる生成内容です`. It returns no annotation UI for
  videos. The hostile-text renderer test and provider boundary tests passed in
  the independent Inner evaluation; security judgment is also assigned separately.
- **AC6:** Composition defaults to enrichment off and checks required project
  configuration when enabled. Make, deployment workflow and Terraform wire both
  service and Import Job. `docs/image-auto-tags.md` explains explicit enable/disable,
  API/IAM/ADC prerequisites, default 50-attempt limit, retry behavior, scoped
  import/backfill, preserved successful output, and size-based freshness limits.
  Search has no Gemini dependency/call. GCS-backed SQLite and OpenCLIP remain.
- **AC7:** `harness/eval/016-image-auto-tags/sample.json` records three actual
  `gemini-3.1-flash-lite` Japanese outputs and three keyword hits after SQLite
  reload with neutral filenames. This reviewer visually inspected the three
  source images: cat, dog and yellow flowers match the broad generated subjects;
  colors, framing and background descriptions are useful search terms. The
  recorded detail/season/impression uncertainty is appropriate: these samples
  establish basic generation/retrieval, not exhaustive precision or category
  classification. The evaluation note explicitly distinguishes local user
  authentication from production Import Job authentication.
- **AC8:** Independent Inner test and code-quality artifacts are PASS, including
  an observed full suite of 143 passed / 1 optional OpenCLIP skip. This product
  PASS supplies one Outer judgment. Remaining Outer reviews, feature verify,
  pre-merge/CI and release verification remain convergence work for the main
  agent/final reviewer; they are not claimed complete by this artifact.

## Scope and remaining delivery work

No blocking product gap found. Generated content remains distinct from manual
metadata, product/SKU identity is not inferred, and reference-category detection
has not been silently added. No broad UI redesign, video tagging, storage/model
migration or unrestricted backfill is introduced.

Production deployment/authentication and final gate convergence are pending at
this review boundary, explicitly tracked by T060/T070. This verdict does not
claim release completion or corpus-wide annotation quality.
