---
id: "005"
status: completed
profile: full
profile_reason: "Constitutional: template history ≠ project history; Adoption command"
---

# Spec: Template Adoption

## Problem

“Use this template” copies template dogfood features into new projects, so the
first product feature becomes `005+` and process history looks like product work.

## Goal

Add `./scripts/adopt` + `docs/ADOPTION.md`, strip known dogfood safely, reset
product docs, add editor/git normalization, and record the constitutional
separation of template vs project history (0.5.0).

## User

Engineers creating a repo from this template; template maintainers adding dogfood.

## Requirements

1. `./scripts/adopt` with fixed dogfood list including this feature
2. Unknown numbered specs → FAIL; already adopted → NO-OP
3. Remove matching harness reviews/context; preserve OS contracts + ADR/REFERENCES
4. Reset PRODUCT/DOMAIN/GLOSSARY from `_templates`
5. `docs/ADOPTION.md` + GitHub settings checklist
6. `.editorconfig` (md trim false) + `.gitattributes`
7. Constitution 0.5.0 + ADR 0012; verify works pre/post adopt

## Acceptance Criteria

1. `scripts/adopt` exists and is executable
2. Dry-run safety: unknown feature causes FAIL (tested in a temp copy)
3. Double-adopt on a stripped tree is NO-OP
4. After adopt in temp copy, `specs/` has no `NNN-*` and verify passes
5. `docs/ADOPTION.md` lists GitHub checklist
6. `.editorconfig` sets `*.md` trim_trailing_whitespace false
7. Constitution Version is 0.5.0; ADR has Sync Impact
8. Full review artifacts for 005 exist

## Out of Scope

- Automating GitHub Rulesets via API
- Deleting ADR/REFERENCES on adopt
- Marker file `.agentic-project` (optional later)

## Constraints

- bash 3.2; FAIL over silent delete; English docs

## Open Questions

None
