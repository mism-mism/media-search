# Curated context: 003-ci-authoritative-merge-gate

## Purpose

CI as authoritative merge-time adapter; status cannot exempt diff-touched gates.

## Decisions

- PR/merge_group = gate; push = health
- draft spec-only limited merge
- BASE_SHA/HEAD_SHA injected by adapter
- Rulesets documented, not automated

## Known limitations

- Without Rulesets, CI does not physically block merge
- Strict draft PRs cannot mix unrelated paths
