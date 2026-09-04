# Plan: Loop Engineering

## Architecture

Add a **control-model** layer between Verify and CI:

```text
… → VERIFY → INNER LOOP → OUTER LOOP (+ Converge) → CI → HUMAN
```

No new executable runner. Documentation + Constitution + agent role labels
encode the contract. Existing hooks/verify/review artifacts remain the
mechanical surface.

## Domain model

| Concept | Meaning |
|---------|---------|
| Inner Converged | FEATURE verify PASS + Inner evaluator PASS |
| Outer Converged | Outer evaluators PASS + no open gap |
| Converge | Outer gap → append tasks → Inner → Outer |
| CI | Enforce claimed convergence |

## Interfaces

- Docs: `docs/LOOPS.md`, Constitution §8, ADR 0013
- Agents: Loop membership labels; `self-reviewer.md`
- Scripts: adopt EXPECTED + verify required_paths only

## Dependency direction

Docs/Constitution → Agents → (existing) Hooks/Verify/CI.  
No new dependency from CI into loop runners.

## Contracts

- Artifact sets for lean/full **unchanged**
- Reviewers remain non-mutating
- `./scripts/loop` MUST NOT exist in v0

## Test strategy

- Meta `./scripts/verify` requires LOOPS + ADR 0013
- FEATURE verify for 006 requires full review set
- Confirm no `scripts/loop` file

## Vertical slice

Constitution bump + LOOPS.md + ADR + agent labels + adopt/verify + dogfood
specs/reviews.

## Risks

- Agents ignore loop docs and open-loop again (mitigation: AGENTS + Implementer)
- Future temptation to automate before Failure Modes (ADR rejects runner in v0)

## Task decomposition

See `tasks.md`.
