# Curated context: 002-lifecycle-hooks

## Purpose

Lifecycle hooks as first-class deterministic enforcement.

## Decisions

- Hook ≠ Verify ≠ Review
- FEATURE-scoped verify; meta-only without FEATURE
- pre-merge uses git diff features + global invariants (not all active)
- A1' structural surfaces require a feature spec in the change
- Implementer≠reviewer not mechanically gated

## Relevant references

- ADR 0009
- `hooks/README.md`
- Constitution §6

## Known limitations

- Spec-exempt allowlist may need extension
- Nested verify output is verbose
- Native agent hook adapters are documentation-only
