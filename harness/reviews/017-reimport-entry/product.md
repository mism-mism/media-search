---
reviewer_role: product-reviewer
reviewer_id: independent-reimport-product-review
---

# PASS

Independent Outer product review of feature 017 against `bcf1cd1` and the
current working tree. No implementation or tests were modified. Unrelated
`.playwright-mcp/` and `014-folder-nav-deep.png` artifacts were excluded.

- **AC1:** The library now presents a native `再取り込み` button immediately
  below upload controls. Its adjacent explanation explicitly states all-folder
  scope, missing image generation, the default limit of 50, and reuse of
  generated content. The toolbar is outside the asset grid and remains present
  when the current folder is empty. Inspected actual Chrome screenshots at
  1280 and 390 pixels: the label and explanation are readable, the control fits
  the viewport, and mobile wrapping preserves the existing layout. The button
  is connected to its explanation with `aria-describedby`.
- **AC2:** The emitted handler posts to `/api/import` without a path override,
  follows the returned job through existing polling, displays queued/running/
  terminal states, and refreshes cards after terminal completion. The supplied
  browser script checks actual button clicks, one POST, completion and refreshed
  generated description at both viewport sizes. The existing endpoint and
  server lock are unchanged.
- **AC3:** A shared busy state is set before enqueue awaits, checked by both
  entry points, and disables both buttons and upload inputs. `finally` restores
  controls. Enqueue and polling exceptions use visible error status; failed jobs
  retain their failure banner. Inspected emitted-handler tests exercise repeated
  clicks, overlap in both directions, success, job failure, request failure,
  polling network failure and the existing upload flow. The independent test
  reviewer observed all five scenarios passing.
- **AC4, review-stage evidence:** Independent test and code-quality reviews
  PASS. The test reviewer inspected the regression result of 148 passed and one
  optional OpenCLIP skip. The real Chrome script uses a controlled API fixture;
  its success evidence and screenshots support the visible entry and event path.
  Failure scenarios are verified through actual emitted handlers with a minimal
  DOM, rather than a production browser session.

The change addresses the reported missing UI entry and updates the previously
misleading usage guidance. There is no new API, folder-scoped import, annotation
behavior, automatic corpus backfill, or reference-image categorization. No
blocking product implementation gaps were found.

This PASS is the pre-release product evaluation, not a claim that AC4 release
work is complete. Complete-artifact hooks, feature verification, pre-merge/CI
and deployment remain tracked in T030/T040 and must complete before overall
completion is claimed. Production IAP browser access was unavailable; no real
corpus import or production inference was run. Record deployment evidence and
these verification limitations in the release report.

## Follow-up review — 2026-09-07, PR #19 comments

Verdict: PASS

Independent Outer reevaluation of the current correction against `origin/main`
at `2d1bedb`, covering AC5–AC7 and T050–T070. The original review and initial
release evidence above remain history. This evaluator changed only this review.

- **AC5:** The real endpoint returns HTTP 409 with object detail containing
  `error: import_busy` and a holder identifier. The shared UI request handler
  now translates that known response into a fixed Japanese explanation that
  another import is running and asks the user to retry after completion. It
  does not expose the holder. Tests assert the actual response shape and exact
  visible message; the whole-script Chrome busy scenario checks the same
  message through the actual button event, without polling.
- **AC6:** A synchronous `ImportResponse` with imported/updated/skipped arrays
  refreshes cards and displays completion without job polling. Controls restore
  through the existing finally path. A malformed nested-job response now shows
  an explicit error instead of the previous false completion. Emitted-handler
  tests cover both cases, and the inspected Chrome script independently
  exercises these branches in the whole rendered script with controlled API
  responses. Async job handling remains intact.
- **AC7:** Toolbar copy explicitly includes images whose generation failed and
  images deferred by the per-import cap. It retains all-folder scope, the
  default 50-image limit and reuse of generated content. Inspected the updated
  390-pixel screenshot: the longer explanation wraps readably and the native
  button remains visible in its row below upload controls.

The three requested corrections are addressed without adding API behavior or
changing import scope. The documented residual-risk dispositions are
proportionate: automatic progress resumption is outside this correction; the
existing server lock still guards execution after polling interruption; the UI
identifies 50 as the default rather than promising the runtime-configured limit.
Whole-script browser checks supplement the regex-extracted handler tests.

Independent Inner reevaluations PASS; the test evaluator directly observed
11 passing targeted tests. The implementer reports 150 regression tests passed
with one optional skip, and five Chrome scenarios passed with no page errors
(desktop/mobile async success, busy conflict, synchronous success and malformed
response). I inspected the browser script and mobile screenshot but did not
rerun these executions. Browser responses are fixtures, not production imports.

No blocking product implementation gap was found. This follow-up PASS is a
pre-release evaluation; current-review lifecycle gates, CI, corrected deployment
and links back to PR #19 comments remain T060/T070 completion obligations. It
does not certify production browser interaction or whole-corpus reimport.
