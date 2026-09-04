# ADR 0014: Portable agent runtime (vendor-neutral roles)

## Context

Loop Engineering (ADR 0013) defines convergence, but roles could still be
documented or automated as if they belonged to one coding-agent vendor.
That would make the Project OS non-portable when Codex, Claude Code, Cursor,
or a future runtime rises or falls.

Failure mode:

> Project OS is invaded by a specific AI vendor/runtime and loses portability.

## Decision

1. Constitution **0.7.0**: agent roles and workflows MUST stay independent of
   specific AI vendors/runtimes (§18); tool bridges remain thin and vendor-native (§17).
2. Add `docs/RUNTIME.md` as the capability + logical-independence contract.
3. LCD = portable Markdown instructions + filesystem + shell — **no** in-repo
   vendor agent CLI wrappers under `scripts/`, `hooks/`, or CI.
4. Self Review may share Implementer context; independent Inner/Outer evaluators
   require a separate role invocation/context (contractual; not identity-gated).
5. FEATURE verify checks `reviewer_role:` **presence** on required evaluator
   artifacts (not `analyze.md`); does not attest identity independence.
6. Update Claude/Cursor shims to tool-native `@AGENTS.md` references; keep
   Gemini/Copilot as thin prose bridges.
7. Dogfood as `specs/007-portable-agent-runtime/`; extend `scripts/adopt` list.

## Alternatives

1. Ship `scripts/run-codex` / `review-with-claude` adapters
2. Require cross-vendor Generator≠Evaluator
3. Mechanically grep-ban vendor CLI strings in v0
4. Fold this into 006 without a new surface

## Consequences

- Runtimes are interchangeable at the OS boundary
- Slightly more docs surface (`RUNTIME.md`)
- Independence remains honor-system except `reviewer_role:` presence
- Personal Agent OS owns vendor launch procedures

## Sync Impact Report

Changed principle(s):

- Vendor/runtime independence of roles and workflows
- Capability-based runtime admission
- Contractual independent evaluator invocation

Affected surfaces:

| Surface | Sync |
|---------|------|
| `CONSTITUTION.md` | 0.7.0; §10; §17–18; tables |
| `docs/RUNTIME.md` | New |
| `docs/LOOPS.md` | Runtime / independence pointers |
| `docs/ARCHITECTURE.md` / `AGENTS.md` / `README.md` | Portable runtime |
| `docs/REFERENCES.md` / `docs/GLOSSARY.md` / `docs/CI.md` | Notes |
| `CLAUDE.md` / `.cursor/rules/agentic-engineering.mdc` | `@AGENTS.md` |
| `agents/*-reviewer.md` / `self-reviewer.md` | Independence notes |
| `scripts/verify` | layout + `reviewer_role:` presence |
| `scripts/adopt` | EXPECTED +007 |
| `specs/007-portable-agent-runtime/` | Dogfood |

Synchronization completed? **yes** (this change set).

## References

- Design grilling (portable agent runtime)
- ADR 0002 (AGENTS.md canonical), 0013 (loops)
- `docs/RUNTIME.md`
- `specs/007-portable-agent-runtime/`
