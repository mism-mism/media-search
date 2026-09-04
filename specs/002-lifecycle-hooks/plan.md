# Plan: Lifecycle Hooks

## Architecture

Five surfaces: Constitution → Rules → Hooks → Verify → Review.
Hooks call verify; CI adapts to `pre-merge`; agent tools adapt to repo hooks (DIP).

## Domain model

Feature states: `draft` → `active` → (hooks…) → `completed`.
`active` ≠ merge-ready; merge readiness is pre-merge over **changed** features.

## Interfaces

```text
./hooks/pre-implement/check [FEATURE]
./hooks/post-implement/check [FEATURE]
./hooks/pre-review/check [FEATURE]
./hooks/pre-merge/check
./scripts/verify [FEATURE]
```

## Dependency direction

```text
CI / Agent runtimes → hooks/*/check → scripts/verify → scripts/lib/*
hooks do not depend on vendor APIs
```

## Contracts

CLI: exit 0 on success; stdout PASS/FAIL/SKIP lines; FEATURE via env or argv.
pre-merge: git diff feature resolution; spec-required path policy (A1').

## Test strategy

Manual executable checks: meta verify; FEATURE verify; pre-implement on active;
pre-merge with FEATURE override; constitution ADR detection via changed files.

## Vertical slice

Ship hooks + verify redesign + constitution/ADR + CI in one feature.

## Risks

- Spec-exempt allowlist gaps
- Nested verify output noise
- First-commit / no-base semver SKIP

## Task decomposition

See `tasks.md`.
