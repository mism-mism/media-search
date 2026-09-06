# Tasks: Japanese image enrichment

- [x] T000 Record accepted scope, model, architecture and checklist.
- [x] T010 Persist separate generated metadata and search it (AC1/AC4).
- [x] T020 Import lifecycle, reuse, failure isolation and bounded calls (AC2/AC3).
- [x] T030 Gemini adapter and configuration with boundary tests (AC5/AC6).
- [x] T040 Add API/card visibility and configuration guidance (AC1/AC5/AC6).
- [x] T050 Run and record small real-image generation/retrieval sample (AC7).
- [x] T060 Independent Inner/Outer reviews and required gates (AC8).
- [x] T070 Release reviewed feature and report production/backfill state.

## Implementation evidence

- Persistence/search: missing domain value (Red), then persistence/search regressions passed.
- Import lifecycle: missing annotation port (Red), then reuse/failure/cap tests passed;
  old connection migration and lost-vector reuse exposed two gaps, fixed and retested.
- Gemini: missing adapter (Red), model-ID validation corrected; malformed/refused output,
  timeout, 403/429 and image bounds covered. Redirect assertion failed before disabling redirects.
- API/UI: absent generated fields/card renderer (Red), then persisted API and escaping passed.
- Runtime: 3 tests failed for missing composition factory/generated output, then wired configuration.
- Full suite: 143 passed, 1 optional OpenCLIP test skipped (model not installed locally).
- Actual Gemini: 3 calls succeeded; 3/3 Japanese query hits after SQLite reload using neutral names.
- Terraform validate passed outside sandbox (provider could not start inside sandbox).
- Deployment env edits are declarative configuration; validated by Terraform and review,
  without writing tests that mirror strings.
- All six independent Inner/Outer evaluator artifacts PASS. Complete-artifact feature verify,
  post-implement, pre-review and commit-scoped pre-merge passed; PR CI run 34038811288 succeeded.
- Production release and service-account Gemini smoke passed. Existing corpus backfill and
  browser-authenticated production upload/search were not run; see
  [release evidence](../../docs/research/016-image-auto-tags-release.md).
