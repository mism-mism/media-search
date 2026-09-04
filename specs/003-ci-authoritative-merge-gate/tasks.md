# Tasks: CI Authoritative Merge Gate

## T001 — verify + resolve-features

- **Objective:** Remove status review SKIP; add bash -n; zero BASE_SHA; draft helper
- **Files likely affected:** `scripts/verify`, `scripts/lib/resolve-features.sh`
- **Dependencies:** none
- **Acceptance Criteria mapping:** AC2–4
- **Verification:** script runs

## T002 — pre-merge draft + health

- **Objective:** draft-spec-only; no_valid_push_base short-circuit
- **Files likely affected:** `hooks/pre-merge/check`
- **Dependencies:** T001
- **Acceptance Criteria mapping:** AC4
- **Verification:** BASE_SHA=0 run

## T003 — workflow + docs + constitution

- **Objective:** YAML adapter; CI.md; 0.3.0; ADR 0010; AGENTS/ARCHITECTURE
- **Files likely affected:** `.github/workflows/verify.yml`, `docs/**`, `CONSTITUTION.md`, `AGENTS.md`
- **Dependencies:** T002
- **Acceptance Criteria mapping:** AC1, AC5, AC6
- **Verification:** grep + layout verify

## T004 — reviews + complete

- **Objective:** full artifacts; status completed
- **Files likely affected:** `harness/reviews/003-*/**`, `specs/003-*/**`
- **Dependencies:** T003
- **Acceptance Criteria mapping:** AC7
- **Verification:** FEATURE verify
