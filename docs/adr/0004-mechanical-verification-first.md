# ADR 0004: Mechanical verification first

## Context

LLM self-judgment is a weak gate. Teams need one command agents can run that
does not lie about what was checked.

## Decision

`./scripts/verify` is the central deterministic interface. Gates report
`PASS`, `FAIL`, or `SKIP(reason=...)`. Unconfigured architecture/security
enforcers must SKIP with `not_configured`, never PASS. Agents must not weaken
rules to obtain green verify.

## Alternatives

1. Prompt-only “please run tests”
2. Fake PASS for missing enforcers
3. Multiple unrelated entry commands with no umbrella

## Consequences

- Honest status for adopters mid-migration
- Early verify output may show many SKIPs until stack adapters exist
- Adopters must wire real enforcers for meaningful assurance

## References

- Backblaze vibe-coding-starter-kit verify / Rule→Enforcer pattern
- `CONSTITUTION.md` §5
- `rules/architecture.md`
