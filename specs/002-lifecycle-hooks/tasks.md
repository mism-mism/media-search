# Tasks: Lifecycle Hooks

## T001 — Shared libs + verify redesign

- **Objective:** status.sh, feature.sh, resolve-features.sh; verify meta vs FEATURE
- **Files likely affected:** `scripts/**`
- **Dependencies:** none
- **Acceptance Criteria mapping:** AC2, AC3
- **Verification:** `./scripts/verify`; `FEATURE=002-lifecycle-hooks ./scripts/verify`

## T002 — Four hooks + README

- **Objective:** pre-implement, post-implement, pre-review, pre-merge
- **Files likely affected:** `hooks/**`
- **Dependencies:** T001
- **Acceptance Criteria mapping:** AC1, AC4
- **Verification:** run each check script

## T003 — Constitution + ADR

- **Objective:** 0.2.0 + ADR 0009 Sync Impact
- **Files likely affected:** `CONSTITUTION.md`, `docs/adr/0009-lifecycle-hooks.md`
- **Dependencies:** T002
- **Acceptance Criteria mapping:** AC6
- **Verification:** grep Version; grep Sync Impact Report

## T004 — Sync docs/agents/CI

- **Objective:** AGENTS, ARCHITECTURE, REFERENCES, README, reviewers metadata, CI
- **Files likely affected:** `AGENTS.md`, `docs/**`, `agents/**`, `.github/workflows/verify.yml`
- **Dependencies:** T003
- **Acceptance Criteria mapping:** AC5, AC7
- **Verification:** workflow contains pre-merge; reviews exist

## T005 — Reviews + mark completed

- **Objective:** full review artifacts + analyze; status completed
- **Files likely affected:** `harness/reviews/002-lifecycle-hooks/**`, `specs/002-lifecycle-hooks/spec.md`
- **Dependencies:** T004
- **Acceptance Criteria mapping:** AC7
- **Verification:** FEATURE verify; pre-merge
