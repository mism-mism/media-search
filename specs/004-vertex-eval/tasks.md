# Tasks: 004 Vertex embeddings evaluation

## Phase 0 — Spec lock

- [x] T000 Clarify Round 1 locked (recommended options)
- [x] T001 Spec AC filled; Vector Search out of scope for 004

## Phase 1 — Harness

- [x] T010 Fixed JA+EN query list checked into `specs/004-vertex-eval/queries.md`
- [x] T011 Script: OpenCLIP baseline import+search → JSON results
- [x] T012 Document Vertex API enablement + ADC for eval project (research note)

## Phase 2 — Vertex adapter spike

- [x] T020 `EmbeddingPort` adapter for Vertex multimodal embeddings
- [x] T021 Separate eval DB path; import same corpus
- [x] T022 Same queries → JSON results; latency/cost notes

## Phase 3 — Decision

- [x] T030 `docs/research/004-vertex-eval.md` with go/no-go (**no-go cutover**)
- [x] T031 Full-profile reviews under `harness/reviews/004-vertex-eval/`
- [x] T032 `FEATURE=004-vertex-eval ./scripts/verify`
- [x] T033 Confirm prod Cloud Run still `EMBEDDER=local` default
