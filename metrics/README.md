# Metrics

Engineering metrics exist to answer:

> Where should we improve the **harness** so human intervention drops?

They are **not** an agent performance scorecard.

## Where recorded

Each feature has `specs/<feature>/metrics.md` (created by `new-feature`).

## Fields

- Feature, PR count, Agent run count, Human intervention count
- Spec-related failure count, Harness-related failure count
- Agent self-correction count, Review loop count
- Time to first working vertical slice, Time to completion

Unknown values: write `unknown` or `not measured`. Do not invent.

## Enforcement

Not a CI gate (v0). Pull request template nudges review of metrics.
