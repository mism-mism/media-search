# ADR 0007: Profile selects assurance by risk

## Context

Teams misuse “small change → less process”. Small security or architecture
changes are high risk. Complex profile matrices (lean + optional reviewers)
become unmaintainable.

## Decision

`profile: lean | full` in `spec.md` front matter selects assurance level by
**change risk**. Architecture, security boundary, constitution, and
cross-boundary contract changes require `full`. No ad-hoc reviewer exception
matrix in v0.

## Alternatives

1. Effort-based ceremony (small/large)
2. à la carte reviewer flags per feature
3. Always-full (too heavy)

## Consequences

- Simple mental model
- Requires honest profile selection (human judgment)
- Verify switches required artifact sets from front matter

## References

- Design grilling Rounds 2–3
- `CONSTITUTION.md` §3
