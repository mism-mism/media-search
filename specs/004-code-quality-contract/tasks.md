# Tasks: Code Quality Contract

## T001 — Rules + agent + architecture boundary

- **Objective:** code-quality.md rules; reviewer; architecture boundary
- **Files likely affected:** `rules/code-quality.md`, `agents/*`
- **Dependencies:** none
- **Acceptance Criteria mapping:** AC3, AC4
- **Verification:** files exist

## T002 — Constitution + verify + docs

- **Objective:** 0.4.0; required sets; ADR; AGENTS/ARCHITECTURE/CI/PR
- **Files likely affected:** `CONSTITUTION.md`, `scripts/verify`, `docs/**`, `.github/**`
- **Dependencies:** T001
- **Acceptance Criteria mapping:** AC2, AC5
- **Verification:** grep + verify layout

## T003 — Retrospective 001–003 + 004 reviews

- **Objective:** Real code-quality artifacts; 004 full set; status completed
- **Files likely affected:** `harness/reviews/**`, `specs/004-*/**`
- **Dependencies:** T002
- **Acceptance Criteria mapping:** AC1, AC6, AC7
- **Verification:** FEATURE verifies
