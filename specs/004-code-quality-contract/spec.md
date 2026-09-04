---
id: "004"
status: completed
profile: full
profile_reason: "Guarantee model: code quality first-class; lean/full require code-quality.md"
---

# Spec: Code Quality Contract

## Problem

Maintainability was implied but not a first-class contract. Lean reviews omitted
code-quality gates; AI over-abstraction risked being mistaken for quality.

## Goal

Define quality as Correctness × Understandability × Changeability × Simplicity;
add `rules/code-quality.md` + `code-quality-reviewer`; require `code-quality.md`
on lean and full; keep mechanical checks honest SKIP until configured;
retrospectively evidence 001–003.

## User

Implementers and reviewers on every feature; adopters wiring stack enforcers later.

## Requirements

1. Constitution 0.4.0 four-axis definition + anti-theater clause
2. `rules/code-quality.md` with Mechanical/Judgment on every rule
3. `agents/code-quality-reviewer.md`; architecture boundary updated
4. lean/full required artifacts include `code-quality.md`
5. verify layout + required set + complexity/dead-code SKIP rows
6. Retrospective real reviews for 001–003
7. ADR 0011 + Sync Impact; docs/PR sync

## Acceptance Criteria

1. `FEATURE=001-template-v0 ./scripts/verify` requires and finds `code-quality.md`
2. lean required set in Constitution/verify includes code-quality
3. `rules/code-quality.md` marks Evaluation on rules
4. Architecture reviewer docs defer local maintainability
5. Constitution Version is 0.4.0; ADR has Sync Impact
6. 001–003 code-quality artifacts contain evidence or N/A with reason
7. Full reviews for 004 exist

## Out of Scope

- Shipping stack-specific complexity/dead-code tools that PASS by default
- Word-ban mechanical lint for utils/helpers
- Grandfathering old features

## Constraints

- Tech-agnostic template; English docs; do not rewrite 001–003 specs (reviews only)

## Open Questions

None
