# Tasks: Media Asset Search Vertical Slice (Local-first)

> Refine file paths after language/FW and vector engine are selected.
> Do not start implementation until `./hooks/pre-implement/check 001-media-asset-search-vertical-slice` passes.

## T001 — Lock runtime + vector engine

- **Objective:** Record language/FW in `docs/ARCHITECTURE.md`; complete engine
  comparison table in `plan.md`; pin semantic-real model/version.
- **Files likely affected:** `docs/ARCHITECTURE.md`, `plan.md`
- **Dependencies:** none
- **Acceptance Criteria mapping:** Constraints (plan-time selections)
- **Verification:** Docs updated; no unresolved product OQs
- **Status:** DONE (2026-09-05) — Python/FastAPI, SQLite+sqlite-vec, OpenCLIP ViT-B-32

---

## T002 — Domain + ports skeleton

- **Objective:** Define MediaAsset model and ports (embed, vector search,
  storage/metadata, media source) with dependency direction tests/stubs.
- **Files likely affected:** TBD (application tree)
- **Dependencies:** T001
- **Acceptance Criteria mapping:** architecture constraints; R17–R19
- **Verification:** unit/direction checks with Fake where applicable

---

## T003 — Import + metadata + upsert

- **Objective:** Directory import, technical metadata, relative-path identity
  upsert, unsupported SKIP+summary; formats JPEG/PNG/MP4 H.264.
- **Files likely affected:** TBD
- **Dependencies:** T002
- **Acceptance Criteria mapping:** AC2, AC3; R1–R7, R27 path
- **Verification:** deterministic tests (Fake)

---

## T004 — Video frames + embedding + local index

- **Objective:** Frame sampling (T=5s / N=3), Fake+Local embedders, local
  vector adapter, collapse max/bestFrame.
- **Files likely affected:** TBD
- **Dependencies:** T003
- **Acceptance Criteria mapping:** AC4, AC6; R8–R12, R17–R20
- **Verification:** Fake wiring tests; prepare semantic-real harness

---

## T005 — Search API (semantic + filters)

- **Objective:** `q` required; mediaType; tags AND; Top-K results with score +
  thumbnail fields.
- **Files likely affected:** TBD
- **Dependencies:** T004
- **Acceptance Criteria mapping:** AC5, AC4; R13–R16
- **Verification:** API tests Fake; golden runner for Real

---

## T006 — Minimal UI + HTTP preview

- **Objective:** Search/filter/results/detail/preview via MediaSource HTTP
  endpoint; video list thumb from bestFrame.
- **Files likely affected:** TBD
- **Dependencies:** T005
- **Acceptance Criteria mapping:** AC1, AC6, AC7; R21–R25
- **Verification:** smoke / acceptance against fixtures

---

## T007 — Container + semantic-real gate + convergence

- **Objective:** Thin compose; model prep docs; wire semantic-real Required
  gate; run full-profile review loop to convergence.
- **Files likely affected:** compose/Docker, scripts, harness reviews
- **Dependencies:** T006
- **Acceptance Criteria mapping:** AC1, AC8, AC9; R26–R29
- **Verification:** deterministic verify + semantic-real PASS + reviews
