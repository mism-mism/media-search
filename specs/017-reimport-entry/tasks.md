# Tasks

- [x] T000 Record the reported missing entry and acceptance criteria.
- [x] T010 Test and implement visible reimport control, progress and mutual exclusion.
- [x] T020 Update guidance and verify rendered UI/regressions.
- [ ] T030 Independent lean reviews, gates and CI.
- [ ] T040 Deploy and record verification.

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
