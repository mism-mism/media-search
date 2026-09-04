# ADR 0005: Independent reviewer

## Context

Implementers (human or agent) exhibit confirmation bias when self-reviewing.
Full Sentinel-style multi-agent review is too heavy for v0.

## Decision

Separate Implementer from Reviewer roles (`agents/*-reviewer.md`).
Required review **artifacts** must exist under `harness/reviews/<feature>/`
before merge review; verify enforces presence by profile (lean/full).
Artifact quality is not judged by CI in v0. Final reviewer is mandatory on
`full` only.

## Alternatives

1. Implementer self-signoff only
2. Full agents-template Sentinel + SHA-bound verdicts in v0
3. Human-only review with no artifact gate

## Consequences

- Lightweight anti-bias control
- Risk of empty/low-quality review files until norms mature (v1 concern)
- Clear extension path to deeper review orchestration

## References

- https://github.com/pedrofuentes/agents-template
- `CONSTITUTION.md` §6
