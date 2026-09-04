# Plan: CI Authoritative Merge Gate

## Architecture

```text
CI (adapter) → pre-merge → verify / lib
```

Authority: Hooks (runtime contract) vs CI (merge authority) vs Rulesets (block merge).

## Domain model

status ≠ inspection scope. draft/active/completed as lifecycle only.

## Interfaces

Workflow env: `BASE_SHA`, `HEAD_SHA`, `MAIN_BRANCH`.  
CLI unchanged: `./hooks/pre-merge/check`, `./scripts/verify`.

## Dependency direction

GitHub Actions → repo hooks → scripts. Hooks do not import Actions APIs.

## Contracts

Workflow YAML is not a policy surface. Required check name is the `verify` job.

## Test strategy

Manual: meta verify; FEATURE=001 reviews enforced; BASE_SHA=0 health SKIP;
pre-merge on current tree; bash -n gate.

## Vertical slice

Constitution + ADR + CI.md + workflow + verify/pre-merge behavior change.

## Risks

- Adopters forget Rulesets → CI green but merge unprotected
- Strict draft-only PRs cannot mix unrelated files

## Task decomposition

See `tasks.md`.
