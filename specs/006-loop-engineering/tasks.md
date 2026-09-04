# Tasks: Loop Engineering

## T001 — Constitution + LOOPS + ADR

- **Objective:** 0.6.0 §8; docs/LOOPS.md; ADR 0013
- **Files likely affected:** `CONSTITUTION.md`, `docs/LOOPS.md`, `docs/adr/0013-loop-engineering.md`
- **Dependencies:** none
- **Acceptance Criteria mapping:** AC1–3
- **Verification:** version grep; files exist

## T002 — Agents + adopt/verify paths

- **Objective:** self-reviewer; Inner/Outer labels; adopt list; verify required_paths
- **Files likely affected:** `agents/**`, `scripts/adopt`, `scripts/verify`
- **Dependencies:** T001
- **Acceptance Criteria mapping:** AC4–7, AC9
- **Verification:** grep Loop membership; no scripts/loop

## T003 — Docs sync + dogfood reviews

- **Objective:** AGENTS/ARCHITECTURE/README/REFERENCES/GLOSSARY; specs/006; full reviews
- **Files likely affected:** `AGENTS.md`, `docs/**`, `README.md`, `specs/006-*/**`, `harness/reviews/006-*/**`
- **Dependencies:** T002
- **Acceptance Criteria mapping:** AC8
- **Verification:** FEATURE=006-loop-engineering ./scripts/verify
