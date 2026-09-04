---
id: "002"
status: completed
profile: full
profile_reason: "Constitutional change: lifecycle hooks as deterministic enforcement"
---

# Spec: Lifecycle Hooks

## Problem

The template had Specs, Rules, Verify, and Review, but no first-class
**deterministic enforcement at agent lifecycle boundaries**. Agents could skip
prep gates; merge could be blocked by unrelated `active` features; verify lied
about feature completeness when run without a feature scope.

## Goal

Add four vendor-neutral hooks, redesign verify scope, enforce pre-merge in CI,
and record the constitutional principle (0.2.0) with ADR + Sync Impact.

## User

Engineers and coding agents using this Project OS; CI on pull requests.

## Requirements

1. Hooks: pre-implement, post-implement, pre-review, pre-merge under `hooks/*/check`
2. Deterministic only; PASS/FAIL/SKIP UX shared with verify
3. verify without FEATURE = meta only; with FEATURE = + completeness
4. pre-merge resolves features from git diff; not all active features
5. Structural contract surfaces require specs in the change (A1')
6. Constitution 0.2.0 + ADR with Sync Impact Report
7. AGENTS/ARCHITECTURE synchronized; CI runs pre-merge

## Acceptance Criteria

1. `./hooks/pre-implement/check 002-lifecycle-hooks` behavior documented; works for `active` features
2. `./scripts/verify` skips feature completeness without FEATURE
3. `FEATURE=002-lifecycle-hooks ./scripts/verify` checks this feature’s reviews/OQ
4. `./hooks/pre-merge/check` runs meta verify + diff features + constitution governance
5. CI workflow invokes pre-merge
6. ADR contains `## Sync Impact Report` and Constitution Version is 0.2.0
7. Independent review artifacts for full profile exist under `harness/reviews/002-lifecycle-hooks/`

## Out of Scope

- Native Claude Code / Git hook config files in-repo
- LLM inside hooks
- Mechanical implementer≠reviewer identity proof
- Empty stub hooks for other lifecycle stages
- verify result caching

## Constraints

- bash 3.2 compatible (macOS); no unnecessary dependencies
- English docs; dogfood with `full` (no bootstrap exception)

## Open Questions

None
