# CI

## Purpose

Provide an **authoritative merge-time** deterministic gate by adapting GitHub
Actions to repository hooks — without embedding policy in YAML and without
running LLM reviewers.

## Authority Model

| Layer | Role |
|-------|------|
| Inner / Outer Loops | Quality **creation** (convergence) — see `docs/LOOPS.md` |
| Agent roles / Runtime | Vendor-neutral contracts + capabilities — see `docs/RUNTIME.md` |
| Hooks | Agent execution-time boundary defense (contract) |
| `./hooks/pre-merge/check` | Merge eligibility policy |
| CI workflow | Thin adapter that *must* run pre-merge |
| Branch protection / Ruleset | Makes the workflow check **required** to block merge |

CI is **not** an Inner/Outer Loop. It enforces a claimed convergence; it does
not run generate→revise cycles.

```text
GitHub Actions  →  ./hooks/pre-merge/check  →  ./scripts/verify + scripts/lib/*
```

Local equivalence: with the same `BASE_SHA` / `HEAD_SHA`,  
`./hooks/pre-merge/check` should match CI.

## Triggers

| Event | Meaning |
|-------|---------|
| `pull_request` | Authoritative merge gate |
| `merge_group` | Authoritative gate for merge queue |
| `push` to `main`/`master` | **Repository health check** (post-hoc) |

Push failures do **not** rewind history. They detect broken main after a direct
push. Real merge defense requires Rulesets + required checks on PR/merge queue.

## Base / Head Resolution

The workflow sets:

- `HEAD_SHA`
- `BASE_SHA` (PR base, merge_group base, or `github.event.before` on push)

Hooks do not interpret GitHub event names. If `BASE_SHA` is all zeros (first
push), pre-merge runs meta verify + `bash -n` and
`SKIP diff-scoped-feature-gates reason=no_valid_push_base`.

## Permissions

```yaml
permissions:
  contents: read
```

CI inspects and fails. It does not write, commit, or approve.

## Concurrency

Same PR’s newer runs cancel in-progress older runs (agentic push frequency).

## Merge Gate

1. Global/meta verify (structure, shims, constitution format, `bash -n`, …)
2. Resolve changed paths (`BASE_SHA...HEAD_SHA`)
3. Spec-escape / structural-surface detection
4. Per diff-touched feature:
   - `draft` + spec/reviews-only → limited gate
   - otherwise → `FEATURE=<id> ./scripts/verify` (reviews required; status≠exemption;
     lean includes **code-quality**)
5. Constitution diff → ADR + Sync Impact + semver bump

## Push Health Check

Same script, post-hoc. Treat as monitoring, not a time machine.

## Required Check Setup

In GitHub **Rulesets** / branch protection for the default branch:

1. Require status checks to pass
2. Add the `verify` workflow job check
3. Do not rely on path-filtered workflows for this required check

## What CI Does Not Do

- Run LLM reviewers
- Judge architecture/product quality beyond artifact presence
- Modify repository contents
- Commit fixes
- Approve PRs
- Replace human judgment
