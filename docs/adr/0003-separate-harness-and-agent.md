# ADR 0003: Separate Harness and Agent

## Context

Agents conflate plans, transcripts, and “done”. Long-running work needs a place
for evidence and curated memory that is not the model context window.

## Decision

Split responsibilities:

- **Agent layer:** roles under `agents/`, judgment, implementation, review opinions
- **Harness layer:** `harness/reviews/` (committed), `harness/context/` (curated
  only), `harness/logs/` (gitignored), plus `./scripts/*`

Raw transcripts and prompt dumps must not be committed.

## Alternatives

1. Everything in `AGENTS.md` / chat history
2. Full Cookbook phase-packet harness mandatory in v0
3. All harness artifacts gitignored (CI-only)

## Consequences

- Auditable completion evidence in-repo
- Discipline required to curate context
- Logs stay local to avoid secrets and repo bloat

## References

- OpenAI Cookbook iterating-development-workflows / harness engineering essay
- `CONSTITUTION.md` §4
- `docs/REFERENCES.md`
