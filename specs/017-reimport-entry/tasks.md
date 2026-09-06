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
