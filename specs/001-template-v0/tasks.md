# Tasks: Template v0

## T001 — Core contracts

- **Objective:** Add CONSTITUTION, AGENTS, shims, gitignore
- **Files likely affected:** `CONSTITUTION.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`, `.cursor/rules/*`, `.gitignore`
- **Dependencies:** none
- **Acceptance Criteria mapping:** AC9/10 precursors; shim rules
- **Verification:** files exist; verify shim gates

## T002 — Docs and ADRs

- **Objective:** PRODUCT, ARCHITECTURE, REFERENCES, ADRs 0001–0008
- **Files likely affected:** `docs/**`
- **Dependencies:** T001
- **Acceptance Criteria mapping:** AC9, AC10
- **Verification:** paths exist

## T003 — Spec templates and dogfood feature

- **Objective:** `_template/` + `001-template-v0/` completed
- **Files likely affected:** `specs/**`
- **Dependencies:** T001
- **Acceptance Criteria mapping:** AC3, AC4, AC8
- **Verification:** structure inspection

## T004 — Agents, rules, harness, metrics

- **Objective:** Role prompts, Rule→Enforcer tables, harness layout
- **Files likely affected:** `agents/**`, `rules/**`, `harness/**`, `metrics/**`
- **Dependencies:** T001
- **Acceptance Criteria mapping:** AC5–7
- **Verification:** verify architecture SKIP; reviews for 001 present (completed exempt)

## T005 — Scripts and CI surface

- **Objective:** bootstrap, new-feature, verify; GitHub workflow + PR template; README
- **Files likely affected:** `scripts/**`, `.github/**`, `README.md`
- **Dependencies:** T002, T003, T004
- **Acceptance Criteria mapping:** AC1–7
- **Verification:** run scripts per AC
