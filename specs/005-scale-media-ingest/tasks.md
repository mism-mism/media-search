# Tasks: Scale media ingest (10k + video)

Verification maps to AC in `spec.md`.

## Clarify / activate

- [x] T000 Lock Round 1+2; `spec.md` → `active`

## Ports + application

- [x] T010 Add `ImportJobPort` + status model
- [x] T020 Add `ImportLockPort`
- [x] T030 Frame durability port
- [x] T040 Wire `ImportDirectory` to FrameStore + progress
- [x] T050 Single-writer around mutate + release in `finally`

## Local adapters + API

- [x] T060 Local job runner + filesystem lock + LocalFrameStore
- [x] T070 API enqueue / status / 409
- [x] T080 UI Import poll + `/api/stats`

## GCP adapters + IaC

- [x] T090 GCS FrameStore; thumbnails via store
- [x] T100 Cloud Run Job adapter + `worker_import`
- [x] T110 Terraform Job + IAM + service env
- [x] T120 GCS lock object

## Docs + verification

- [x] T130 `docs/run-gcp.md` scale section
- [x] T140 Tests (lock, cold wipe, API jobs)
- [x] T150 post-implement / verify
- [x] T160 Outer reviews under `harness/reviews/005-scale-media-ingest/`
