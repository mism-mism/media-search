# ADR 0009: Lifecycle hooks as deterministic enforcement points

## Context

v0 standardized Specs, Rules, Verify, and Review, but lacked first-class
**lifecycle boundaries** where deterministic policy runs. Relying on agent
compliance alone allows skipping Open Question gates, feature-scoped verify,
and merge requirements. This is a constitutional gap relative to the principle
that deterministic checks belong in code and judgment belongs to reviewers.

## Decision

1. Add vendor-neutral executable hooks:
   - `hooks/pre-implement/check`
   - `hooks/post-implement/check`
   - `hooks/pre-review/check`
   - `hooks/pre-merge/check`
2. Hooks are **deterministic only** (no LLM calls). Reviewers remain the
   non-deterministic judgment layer.
3. `./scripts/verify` remains the completion verifier:
   - no `FEATURE` → global/meta only (`SKIP feature-completeness reason=no_feature_scope`)
   - with `FEATURE` → meta + feature completeness
4. CI mechanically runs `pre-merge` (diff-scoped features + global invariants).
5. Agent runtimes adapt *to* repo hooks (DIP); native Claude/Git hook wiring is
   documented, not mandated as template files in v0.
6. Bump Constitution to **0.2.0** with the hooks principle.

## Alternatives

1. Prompt-only lifecycle reminders in `AGENTS.md` (no executables)
2. Vendor-native hooks only (Claude Code / Git) as the SoT
3. Expand to every lifecycle stage with empty stub hooks
4. Keep verify checking all active features for reviews (blocks parallel work)

## Consequences

- Clear separation: Hook timing vs Verify correctness vs Review judgment
- Parallel `active` features no longer block unrelated merges
- Agents must run feature-scoped verify to claim completion
- Spec-exempt allowlist must be maintained carefully (A1')
- Implementer≠reviewer remains a human/contract concern in v0

## Sync Impact Report

Changed principle(s):

- Deterministic policy enforcement at lifecycle boundaries via executable hooks
- Verify scope model (`no_feature_scope` vs `FEATURE=…`)
- Structural contract surfaces require a feature spec in the change set

Affected surfaces:

| Surface | Sync |
|---------|------|
| `CONSTITUTION.md` | Version 0.2.0; new §6 Hooks; verify scope; structural surfaces |
| `AGENTS.md` | Lifecycle hook obligations; feature-scoped verify |
| `docs/ARCHITECTURE.md` | Five-surface diagram (Constitution/Rules/Hooks/Verify/Review) |
| `rules/*` | No policy change; pointer via Architecture |
| `agents/*` | Optional review artifact metadata; implementer lifecycle notes |
| `hooks/**` | New first-class tree |
| `scripts/verify` + `scripts/lib/*` | Shared status + feature resolve + redesign |
| `.github/workflows/verify.yml` | Runs `pre-merge` |
| `specs/_template` / `specs/README` | Status/profile/hook notes |
| `docs/REFERENCES.md` | Hook lineage note |
| `README.md` | Commands + limitations |

Synchronization completed? **yes** (this change set).

## References

- Design grilling (lifecycle hooks rounds)
- `CONSTITUTION.md` §6
- Spec Kit / Backblaze (mechanical gates inspiration; not copied)
- `specs/002-lifecycle-hooks/`
