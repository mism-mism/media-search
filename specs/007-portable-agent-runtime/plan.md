# Plan: Portable Agent Runtime

## Architecture

```text
Project OS (Spec/Rules/Hooks/Loops)
  → Agent Role Contract
  → Runtime Capability Contract
  → Codex | Claude | Cursor | …
```

No adapter layer beyond thin Markdown bridges. LCD = files + shell.

## Domain model

| Concept | Meaning |
|---------|---------|
| Role contract | `agents/*.md` — vendor-neutral |
| Capability | What a runtime must do |
| Logical independence | Separate invocation for independent evaluators |
| Bridge | Tool-native pointer to `AGENTS.md` |

## Interfaces

- Docs: RUNTIME.md, Constitution §18, ADR 0014
- Verify: layout paths + `reviewer_role:` presence
- Shims: CLAUDE / Cursor `@AGENTS.md`

## Dependency direction

OS → roles → capabilities → runtimes. Never reverse.

## Contracts

- scripts/hooks/CI must not invoke vendor agent CLIs
- Independence contractual; presence check only for `reviewer_role:`

## Test strategy

- Meta verify includes RUNTIME + ADR 0014
- FEATURE=007 full reviews with reviewer_role
- Optional negative: strip reviewer_role → fail (manual/dogfood note)

## Risks

- Honor-system independence ignored → document clearly; escalate later
- Grep ban deferred → accept until real Failure Mode

## Task decomposition

See `tasks.md`.
