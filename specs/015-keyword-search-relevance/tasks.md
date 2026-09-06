# Tasks: Reliable keyword search

- [x] T010 Reproduce and repair SQLite tag string matching (AC1).
- [x] T020 Cover and fix keyword-first text ranking, deterministic ties and preserved filters (AC2–AC3).
- [x] T030 Verify GET/POST with SQLite and document ordering (AC3).
- [x] T040 Run lifecycle checks, independent Inner/Outer reviews and final gates (AC4).

## Observed verification

- Before production edits: `.venv/bin/python -m pytest -q tests/test_keyword_search.py`
  → 21 failed, 21 passed. Failures reproduce Japanese/escaped tag omissions,
  JSON-syntax false positives, keyword displacement and unstable text ties.
- After edits: keyword, product-search, search-use-case, performance-009 and
  API-search suites → 60 passed.
- Initial post-implement and pre-review checks: full test suite → 94 passed,
  1 skipped (opt-in OpenCLIP smoke); feature gate fails only for
  missing independent review artifacts. Re-run after actual reviews exist.
- No model-quality benchmark or production deployment is claimed.

## Completion evidence

- Original Japanese-tag and top-one reproductions now both PASS.
- Independent Inner test/code-quality and Outer product reviews: PASS under
  `harness/reviews/015-keyword-search-relevance/`.
- Post-implement and pre-review reruns: PASS, including feature-scoped verify.
- `FEATURE=015-keyword-search-relevance ./hooks/pre-merge/check`: PASS.
- Default `./hooks/pre-merge/check`: PASS (existing branch feature 014 scope).
  Feature 015 was explicitly scoped above because its changes are uncommitted.
- Final full suite: 94 passed, 1 opt-in OpenCLIP smoke skipped; two dependency
  deprecation warnings. Unconfigured static/integration gates report SKIP.
- Inner and Outer converged for this bounded feature. Remote CI, commit, merge
  and deployment were not performed.

## Release follow-up (human requested 2026-09-06)

- [ ] T050 Commit the reviewed correction, pass PR CI and merge.
- [ ] T060 Deploy using the existing procedure; verify the ready revision,
  preserved IAP protection and authenticated search when available.

Pre-release production revision: `media-search-00021-f5l` (100% traffic, IAP
enabled). GitHub deploy run 33972766254 failed for missing auth configuration;
use the documented `make deploy` path for this release.
