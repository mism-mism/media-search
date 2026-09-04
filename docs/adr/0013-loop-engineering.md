# ADR 0013: Loop Engineering as convergence control

## Context

The template had Spec, Hooks, Verify, Reviewers, Converge (principle), and CI,
but “done” was still a chain of handoffs without an explicit **convergence**
model. Industry practice is moving from Harness Engineering toward Loop
Engineering (inner generate→review→revise; outer feature evaluation). Open-loop
PR-once delivery underperforms closed loops.

## Decision

1. Add **Loop Engineering** as a first-class surface: Inner Loop, Outer Loop,
   Converge-as-outer-gap-protocol, Human escalation, CI-is-not-a-loop.
2. Document in Constitution (0.6.0) and `docs/LOOPS.md`.
3. **Do not** ship a loop orchestrator/`./scripts/loop` in v0.
4. Keep lean/full **required artifact sets unchanged**; classify existing
   reviewers as Inner vs Outer.
5. Add optional `agents/self-reviewer.md`; `self.md` not verify-gated.
6. Converge remains append-only tasks on Outer gap — no new hook.
7. Implementer mutates; Evaluators evaluate only; CI enforces.
8. Update `scripts/adopt` EXPECTED list with `006-loop-engineering`.

## Alternatives

1. Automate loops with a runner in v0
2. Restructure required review artifacts around Inner/Outer
3. Allow reviewers to fix and self-PASS
4. Drop the Converge name entirely

## Consequences

- Clear definition of Inner/Outer converged
- Slightly more conceptual surface; no new mandatory ceremony files
- Runner automation deferred until adopting projects prove the need
- adopt list maintenance continues

## Sync Impact Report

Changed principle(s):

- Inner/Outer Loop convergence control
- CI separated from quality-creation loops
- Converge = Outer gap append-only protocol

Affected surfaces:

| Surface | Sync |
|---------|------|
| `CONSTITUTION.md` | 0.6.0; §8 Loops; surfaces table |
| `docs/LOOPS.md` | New |
| `docs/ARCHITECTURE.md` | Loops in diagram |
| `AGENTS.md` / `README.md` | Loop pointers |
| `agents/self-reviewer.md` | New |
| `agents/implementer.md` / `*-reviewer.md` | Inner/Outer labels |
| `scripts/adopt` | EXPECTED +006 |
| `scripts/verify` | layout: LOOPS.md, ADR 0013 |
| `docs/REFERENCES.md` | Loop Engineering note |
| `specs/006-loop-engineering/` | Dogfood |

Synchronization completed? **yes** (this change set).

## References

- Design grilling (Loop Engineering)
- Microsoft LoopsBench / “From Harness Engineering to Loop Engineering” (2025–2026 discourse)
- OpenAI harness / multi-agent review loops (operational pattern)
- Anthropic planner–generator–evaluator experiments (pattern reference)
- `docs/LOOPS.md`
- `specs/006-loop-engineering/`
