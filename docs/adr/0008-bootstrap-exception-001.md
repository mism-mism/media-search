# ADR 0008: Bootstrap exception for specs/001-template-v0

## Context

Creating the template necessarily established Constitution, AGENTS, harness, and
verify before those rules could govern the work.

## Decision

`specs/001-template-v0/` is recorded as a **bootstrap exception** that
establishes governance subsequently applied to the repository. It remains
`status: completed` as dogfood evidence. **No further exceptions** are allowed;
later template changes must follow dogfood tiers in `CONSTITUTION.md`.

## Alternatives

1. Pretend v0 was produced under full governance (false history)
2. Omit any completed spec (weaker dogfood proof)

## Consequences

- Honest provenance
- Clear “from here on, no exceptions” line
- Example feature layout for adopters

## References

- Design grilling Round 2 Q12
- `CONSTITUTION.md` §11
- `specs/001-template-v0/`
