# ADR 0002: AGENTS.md is canonical

## Context

Claude, Codex, Cursor, Copilot, and Gemini each discover instructions differently.
Duplicating policy across tool files causes drift and contradictory rules.

## Decision

`AGENTS.md` is the single canonical agent contract. Tool files
(`CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`,
`.cursor/rules/agentic-engineering.mdc`) are thin adapters that only point to
`AGENTS.md`. `./scripts/verify` checks shim presence, AGENTS reference, and
size budgets.

## Alternatives

1. Per-tool full policy copies
2. AGENTS.md only with no shims (discovery failures on some tools)
3. Hidden `.agent/` instruction trees as primary SoT

## Consequences

- Portable across tools
- Policy edits happen in one place
- Shims must stay tiny; verify enforces budgets

## References

- https://github.com/indisoluble/AGENTS-spec
- https://github.com/backblaze-b2-samples/vibe-coding-starter-kit
- https://github.com/openai/openai-cookbook (AGENTS as TOC pattern)
- `CONSTITUTION.md` §12
