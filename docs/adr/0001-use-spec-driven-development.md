# ADR 0001: Use Spec-Driven Development

## Context

AI agents implement quickly but invent requirements when specs are vague.
We need a durable source of truth for intended behavior that is independent of
any single AI vendor or chat transcript.

## Decision

Adopt Spec-Driven Development with feature directories under `specs/NNN-name/`,
artifacts `spec.md`, `clarify.md`, `plan.md`, `tasks.md`, `checklist.md`, and
`metrics.md`. Specs own Acceptance Criteria; agents must not silently fill gaps.

## Alternatives

1. Chat-only tasking with no persistent specs
2. Issues/tickets as the only SoT
3. Full GitHub Spec Kit `.specify/` + CLI as hard dependency

## Consequences

- Clear audit trail from intent to tasks
- Upfront clarification cost for ambiguous work
- Need lean/full profiles to avoid ceremony on low-risk changes

## References

- https://github.com/github/spec-kit
- `docs/REFERENCES.md` (Spec Kit section)
- `CONSTITUTION.md` §2
