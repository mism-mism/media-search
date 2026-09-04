# ADR 0012: Template adoption separates dogfood from projects

## Context

GitHub “Use this template” copies the entire tree, including template dogfood
features `001`–`00N` and their review artifacts. Adopting products would then
start at `005+` and inherit unrelated process history as if it were product
work. CI/docs alone cannot fix this; an explicit Adoption step is required.

## Decision

1. Add Constitution principle: template history ≠ project history; Adoption
   removes dogfood while preserving Project OS contracts and provenance
   (ADR/REFERENCES).
2. Add `./scripts/adopt` (separate from `bootstrap`):
   - Deletes only a **fixed** dogfood feature list
   - **FAIL** if unknown `specs/NNN-*` exist
   - **NO-OP** if already adopted (no dogfood features left)
   - Resets PRODUCT/DOMAIN/GLOSSARY from `docs/_templates/`
   - Runs `./scripts/verify`
3. Add `docs/ADOPTION.md` with GitHub repository settings checklist.
4. Add minimal `.editorconfig` (Markdown does **not** trim trailing whitespace)
   and `.gitattributes` (LF normalization).
5. Bump Constitution **0.4.0 → 0.5.0**.

## Alternatives

1. Document manual deletion only
2. `bootstrap --adopt` flag
3. Move dogfood into `docs/template-history/` inside adopting repos
4. Delete ADR/REFERENCES on adopt

## Consequences

- Fresh projects start features at `001`
- Template maintainers must update the fixed list when adding dogfood features
- Accidentally running adopt on a repo with real features fails closed
- Provenance of the OS remains in ADR/REFERENCES

## Sync Impact Report

Changed principle(s):

- Template vs project history separation
- Adoption as first-class initialization

Affected surfaces:

| Surface | Sync |
|---------|------|
| `CONSTITUTION.md` | 0.5.0; §1 Adoption sentence |
| `scripts/adopt` | New |
| `docs/ADOPTION.md` | New |
| `docs/_templates/PRODUCT.md` | New |
| `.editorconfig` / `.gitattributes` | New |
| `scripts/verify` | Layout; optional 001 dogfood |
| `AGENTS.md` / `README.md` / `docs/ARCHITECTURE.md` | Sync |
| `specs/005-template-adoption/` | Dogfood feature |

Synchronization completed? **yes** (this change set).

## References

- Design grilling (template adoption)
- `docs/ADOPTION.md`
- `specs/005-template-adoption/`
