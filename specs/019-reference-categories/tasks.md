# Tasks and test list
- [x] T000 Record model, boundaries, AC and operational caps.
- [x] T010 Domain/report and SQLite catalog/persistence/search tests, Red→Green.
- [x] T020 Import reuse/failure/cap and Gemini strict multimodal tests, Red→Green.
- [x] T030 Management API, safe uploads, shared worker wiring and visible UI.
- [x] T040 Browser verification, bounded real sample and operator documentation.
- [x] T050 Independent Inner/Outer evaluations, gates, commit and PR/CI.

## Inner review iteration 1
- [x] T060 Reviewer found equal-byte-length replacement incorrectly reused matches;
  add content SHA-256 provenance, re-read enabled classification targets and
  invalidate stale reports on changed bytes even when size is unchanged.
- Red: initial category domain/import collection failed (2e12f237); 54 relevant
  tests Green (70a9b31e). Provider Red missing adapter (f7589656), 28 Green
  (37eb8f3a). API Red missing runtime wiring (e0ce2a76), then Green.
- Initial full suite: 176 passed / 1 optional OpenCLIP skipped (ef1e8dc8).
- Initial post-implement / pre-review failed only absent evaluator artifacts;
  actual suite passed. Never represented missing reviews as PASS.
- Equal-length replacement Red: b2ebdf6d; targeted Green: 011c0692.
- Browser at 1280px / 390px used actual local FastAPI/SQLite endpoints, actual
  image uploads and Chrome. Register/preview/delete/escaped text/import entry
  passed, no page errors or horizontal overflow. Gemini was off for browser
  verification. /private/tmp/media-search-019-browser.cjs and screenshots.

## Outer review iteration 1
- [x] T070 Product evaluator found cached/in-flight search responses could show
  obsolete category matches after catalog changes. Clear search cards/count and
  invalidate request generation immediately after successful create/delete.
- Browser Red: harness/eval/019-reference-categories/browser.cjs failed with
  stale search card count 1 after catalog creation (expected0).
- [x] T080 Reevaluate Inner and Product/Final after rendered create/delete +
  delayed response regression, then rerun all required gates and PR CI.

- T070 browser Green: four scenarios passed; independent Inner addenda PASS.
- Final implementation suite: 180 passed / 1 optional OpenCLIP skip (4e75fa5d).

## PR handoff (2026-09-07 JST)

- Separate worktree `/private/tmp/media-search-019-reference-categories`, branch
  `feature/019-reference-categories`; implementation d4afe18, main synchronization
  3faa9d2 includes merged scale-to-zero PR21 without changing its settings.
- PR https://github.com/mism-mism/media-search/pull/22 is open for review;
  category feature is not merged or deployed and no production corpus import ran.
- Independent full Inner + Outer reviews PASS. Completed-artifact post-implement
  (3205c919), pre-review (b75555b5), feature-scoped nested verify and exact
  diff-scoped pre-merge (e7d5ea8b, then fed03875 after main synchronization) PASS.
- Code-head GitHub CI 34045234526 succeeded, including authoritative pre-merge.
  This final documentation update remains subject to its own CI run.
- Actual Chrome management checks passed at 1280/390px after the final UI fix;
  four cached/delayed search invalidation scenarios passed. Local test server
  was stopped after validation.
- Real Gemini calls were limited to three; source and quality limitations remain
  explicit in docs/research/019-reference-category-eval.md. No additional cloud
  resources were created for this feature.
