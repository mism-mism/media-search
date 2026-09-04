# Tasks: Template Adoption

## T001 — adopt + templates + editor/git

- **Objective:** scripts/adopt; PRODUCT template; editorconfig; gitattributes
- **Files likely affected:** `scripts/adopt`, `docs/_templates/PRODUCT.md`, `.editorconfig`, `.gitattributes`
- **Dependencies:** none
- **Acceptance Criteria mapping:** AC1, AC6
- **Verification:** executable; editorconfig grep

## T002 — docs + constitution + verify

- **Objective:** ADOPTION.md; 0.5.0; ADR 0012; verify layout/dogfood optional
- **Files likely affected:** `docs/**`, `CONSTITUTION.md`, `scripts/verify`
- **Dependencies:** T001
- **Acceptance Criteria mapping:** AC5, AC7
- **Verification:** verify meta

## T003 — reviews + acceptance in temp copy

- **Objective:** full reviews; temp adopt tests
- **Files likely affected:** `harness/reviews/005-*/**`, `specs/005-*/**`
- **Dependencies:** T002
- **Acceptance Criteria mapping:** AC2–4, AC8
- **Verification:** temp copy scripted checks
