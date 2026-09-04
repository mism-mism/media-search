# Tasks: Portable Agent Runtime

## T001 — Constitution + RUNTIME + ADR

- **Objective:** 0.7.0 §18; RUNTIME.md; ADR 0014
- **Files likely affected:** `CONSTITUTION.md`, `docs/RUNTIME.md`, `docs/adr/0014-portable-agent-runtime.md`
- **Dependencies:** none
- **Acceptance Criteria mapping:** AC1–3
- **Verification:** version + files exist

## T002 — Shims + verify + adopt + agent labels

- **Objective:** @AGENTS bridges; reviewer_role check; adopt +007; agent independence notes
- **Files likely affected:** `CLAUDE.md`, `.cursor/rules/*`, `scripts/*`, `agents/*`
- **Dependencies:** T001
- **Acceptance Criteria mapping:** AC4–7, AC9
- **Verification:** shim verify; FEATURE role check

## T003 — Docs sync + dogfood reviews

- **Objective:** AGENTS/LOOPS/ARCHITECTURE/README/REFERENCES/GLOSSARY/CI; specs/007; reviews
- **Files likely affected:** `docs/**`, `AGENTS.md`, `README.md`, `specs/007-*/**`, `harness/reviews/007-*/**`
- **Dependencies:** T002
- **Acceptance Criteria mapping:** AC8
- **Verification:** FEATURE=007-portable-agent-runtime ./scripts/verify
