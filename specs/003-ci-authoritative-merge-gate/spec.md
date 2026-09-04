---
id: "003"
status: completed
profile: full
profile_reason: "Constitutional: CI authoritative merge gate + status≠exemption"
---

# Spec: CI Authoritative Merge Gate

## Problem

Merge authority was under-specified: CI was a thin workflow without a clear
authority model, and feature-scoped verify skipped reviews for `completed`/
`draft`, enabling status-flip gate evasion.

## Goal

Make CI the authoritative merge-time adapter for `pre-merge`, separate push
health checks from merge gates, and ensure diff-touched features are never
exempted by lifecycle status (with a draft spec-only exception).

## User

Engineers configuring GitHub Rulesets; agents preparing PRs; CI runners.

## Requirements

1. Workflow: `pull_request` + `merge_group` + `push` main/master
2. Thin adapter only → `./hooks/pre-merge/check` with BASE_SHA/HEAD_SHA
3. permissions read-only; concurrency cancel-in-progress; no paths filter
4. No LLM in CI
5. verify: status does not skip reviews when FEATURE set
6. pre-merge: draft spec-only limited gate; invalid BASE_SHA health fallback
7. Constitution 0.3.0 + ADR 0010 Sync Impact + docs/CI.md

## Acceptance Criteria

1. `.github/workflows/verify.yml` matches the adapter contract above
2. `./scripts/verify` includes `bash -n` and does not skip reviews by status
3. `FEATURE=001-template-v0 ./scripts/verify` still requires lean review files
4. `BASE_SHA=0000… ./hooks/pre-merge/check` SKIPs diff-scoped feature gates
5. docs/CI.md documents required check setup and “CI does not…”
6. Constitution Version is 0.3.0; ADR has Sync Impact Report
7. Full review artifacts exist for this feature

## Out of Scope

- Configuring Rulesets inside GitHub for adopters (docs only)
- LLM reviewers in CI
- `004-code-quality-contract`
- Reference/link crawlers

## Constraints

- bash 3.2; DIP (hooks GitHub-agnostic); English docs; do not rewrite 002

## Open Questions

None
