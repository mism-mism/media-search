# Specs

Feature work lives here. Each feature is `NNN-short-name/` with sequential
`NNN` assigned by `./scripts/new-feature` (numbers have no semantic meaning).

## Create a feature

```bash
./scripts/new-feature asset-search
# → specs/00N-asset-search/
```

## Artifacts

| File | Role |
|------|------|
| `spec.md` | Problem, Goal, Requirements, Acceptance Criteria, Out of Scope, Constraints, Open Questions; front matter owns `profile` |
| `clarify.md` | Ambiguities, Questions, Decisions, Unresolved |
| `plan.md` | Architecture, domain, interfaces, dependency direction, tests, risks, tasks decomposition; Contracts when boundaries change |
| `tasks.md` | Executable tasks with verification mapping |
| `checklist.md` | Requirements-quality checklist (not “code done”) |
| `metrics.md` | Engineering metrics for harness improvement (non-gating) |

## Profiles

Set in `spec.md` front matter:

```yaml
---
id: "002"
status: active
profile: lean
# profile_reason: "optional note"
---
```

Statuses: `draft` (not implementable) → `active` (implementation permitted) →
`completed` (historical).

See `CONSTITUTION.md` for lean vs full paths, hooks, and review artifacts
(lean Inner: test + code-quality; lean Outer: product). Drive work through
Inner then Outer loops ([`docs/LOOPS.md`](../docs/LOOPS.md)).

## Lifecycle hooks

Before implement / after implement / before review / before merge — see
[`hooks/README.md`](../hooks/README.md).

## Open Questions

Unresolved items that affect Domain, Constraints, or Acceptance Criteria:
agents **stop**. Humans decide; decisions are recorded in `clarify.md`.
