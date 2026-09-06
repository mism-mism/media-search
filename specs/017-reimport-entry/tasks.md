# Tasks

- [x] T000 Record the reported missing entry and acceptance criteria.
- [x] T010 Test and implement visible reimport control, progress and mutual exclusion.
- [x] T020 Update guidance and verify rendered UI/regressions.
- [x] T030 Independent lean reviews, gates and CI.
- [x] T040 Deploy and record verification.

## Observed implementation evidence

- Red: five UI scenarios failed because the button was absent (8c091437).
- Green: the five emitted-handler tests passed (20d704c2), covering success,
  failed job, enqueue 409, polling network failure and existing upload flow.
- Full suite: 148 passed / 1 optional OpenCLIP skipped (ac064808).
- Real Chrome with controlled API responses: visible native button at 1280px
  and 390px, one POST /api/import, disabled concurrent actions, terminal status
  and refreshed generated annotation; no page errors. No production import run.
- Browser script: /private/tmp/media-search-017-browser.cjs. Screenshot evidence:
  /private/tmp/media-search-017-1280.png and /private/tmp/media-search-017-390.png.
- Initial hooks passed runtime/meta checks but failed missing independent review
  artifacts. Review directory created; complete-artifact hooks will be rerun.

## Release evidence (2026-09-07 JST)

- Independent lean test/code-quality/product reviews PASS. Complete-artifact
  post-implement, pre-review and commit-scoped pre-merge gates PASS.
- PR #19 code CI run 34041036131 succeeded; repository's external review checks
  also succeeded. Reviewed implementation commit: e0ae106f6c1b9ac5f3ee55576b15d25384f1cef9.
- Deployed image: `017-e0ae106`; digest
  `sha256:32780930aa33243f386d4e4f98dad45fcd20874ee4996ed954cad7c1ecabc4e0`.
- Cloud Run revision `media-search-00024-lfc` serves 100% traffic; Import Job
  updated to the same image. Anonymous /health remains HTTP302 through IAP.
- Deployment log: /private/tmp/media-search-017-logs/logs/2026-09-07/00cf8999-9289-4f11-ad42-142a86ec4124/.
- Browser click flow used controlled API responses locally. Logged-in production
  browser interaction and actual whole-corpus reimport were not executed.
- User entry: reload the page → ライブラリ → below upload controls → 再取り込み.

## PR #19 review follow-up (2026-09-07)

The external review comments were not handled before the initial merge. Preserve
that release history above; reopen this feature for the requested corrections.

- [x] T050 Match the real busy response, cover synchronous/unknown responses, and clarify retry targets (AC5–AC7).
- [x] T060 Independent lean reevaluation, lifecycle gates and CI for the correction.
- [x] T070 Deploy the correction and link evidence back to the PR #19 comments.

### Follow-up evidence and review disposition

- PR19 discussion_r3944364304: changed the 409 fixture to object detail matching the server;
  fixed Japanese busy text asserted, holder not shown. Red actual generic 409 text,
  then Green with explicit import_busy translation.
- PR19 discussion_r3944364305: added sync summary scenario (one POST/no GET,
  one card refresh/success/re-enabled controls). Also added nested job response failure
  test; it exposed a false success banner, fixed by accepting only known shapes.
- Review prose item 3: toolbar now explicitly includes failed and cap-deferred images.
- Full suite: 150 passed, 1 optional OpenCLIP skip, log c097aee4 under
  /private/tmp/media-search-017-followup-logs/logs/2026-09-07/.
- Remaining risk dispositions: network/poll interruption retains the existing
  server lock; this correction makes the next 409 understandable, without adding
  an unrequested automatic progress-resumption workflow. The label says default 50,
  not the configured absolute limit; runtime config remains documented separately.
  Regex handler tests are supplemented by actual Chrome executing the whole script.
  Independent review is by separate role invocation (docs/RUNTIME.md), not distinct
  commits; all 3 independent roles are being rerun for this correction.

### Follow-up delivery (2026-09-07 JST)

- All 3 independent lean follow-up evaluations PASS; lifecycle/pre-merge gates
  passed; code CI run 34042249007 succeeded. Bugbot completed with no findings;
  its review body and inline comments were explicitly checked.
- Real Chrome whole-script scenarios passed: desktop/mobile success, real 409 busy,
  synchronous summary, and malformed nested-job response; zero page errors.
- Deployed implementation 66b6ffa as `017-66b6ffa`, digest
  `sha256:5edfc923ea73a298b93034c370c1a549eeb41fe15752e5147844c936c5efbcd1`.
  Cloud Run revision `media-search-00025-66t` Ready and 100% traffic; Import Job
  updated. IAP enabled, anonymous /health HTTP 302. No actual corpus import executed.
- Replied with correction/evidence/PR #20 to both original threads:
  https://github.com/mism-mism/media-search/pull/19#discussion_r3944423590
  https://github.com/mism-mism/media-search/pull/19#discussion_r3944423663
- Deployment log:
  /private/tmp/media-search-017-followup-logs/logs/2026-09-07/fca10196-a0d4-494c-8aa9-347ed49a56c7/.
- Logged-in production browser interaction was not performed. Review-thread
  resolution and final merge state are recorded on PR #20 after final checks.
