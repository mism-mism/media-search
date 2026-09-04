# ADR 0006: Portable Project OS (no personal OS dependency)

## Context

The maintainer has a personal Agent OS (global rules, orchestration). Baking it
into the template would break portability and invert dependencies.

## Decision

This template is a **Portable Project OS**. It must not reference or require
personal Agent OS components. Personal tooling may optionally adapt *to* the
Project OS (DIP-style).

## Alternatives

1. Integrate Herdr/TM/global rules as hard requirements
2. Dual-mode template (personal vs portable) with conditional docs

## Consequences

- Works for any adopter
- Maintainer may still accelerate via personal adapters outside this repo
- Template docs stay vendor- and person-agnostic

## References

- Design grilling Round 1 Q1
- `CONSTITUTION.md` §1
