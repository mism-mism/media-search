---
id: "006"
status: completed
profile: full
profile_reason: "Constitutional: Loop Engineering as first-class convergence control"
---

# Spec: Loop Engineering

## Problem

Implement → Review → Fix are scattered across hooks, verify, and reviewers, so
“done” is undefined. Teams treat CI or a single review pass as convergence.

## Goal

Add **Loop Engineering** as a first-class control surface: Inner Loop (task),
Outer Loop (feature/system), Converge (append-only on Outer gaps), with CI
explicitly **not** a loop. v0 is **contract-only** (no `./scripts/loop` runner).

## User

Engineers and agents using this Project OS; template maintainers dogfooding.

## Requirements

1. Constitution 0.6.0 with § Loop engineering; surfaces table updated
2. `docs/LOOPS.md` defines Inner/Outer/Converge/CI/Human and mutation rules
3. ADR 0013 records decision + Sync Impact
4. Classify existing lean/full artifacts as Inner vs Outer (sets unchanged)
5. `agents/self-reviewer.md` (optional Inner); Implementer as mutator
6. Outer `final` covers cross-task/regression (no new artifact file)
7. `scripts/adopt` EXPECTED list includes `006-loop-engineering`
8. verify requires `docs/LOOPS.md` and ADR 0013
9. AGENTS / ARCHITECTURE / README / REFERENCES / GLOSSARY synced

## Acceptance Criteria

1. Constitution Version is 0.6.0; §8 defines Inner/Outer/Converge; CI ≠ loop
2. `docs/LOOPS.md` exists and matches Constitution contract
3. ADR 0013 exists with Sync Impact
4. lean/full required artifact sets unchanged; docs classify Inner vs Outer
5. `agents/self-reviewer.md` exists; reviewer agents labeled Inner/Outer
6. `scripts/adopt` lists `006-loop-engineering`
7. Meta verify requires LOOPS.md + ADR 0013
8. Full review artifacts for 006 exist and PASS
9. No `./scripts/loop` shipped

## Out of Scope

- Automated loop runner / state machine
- Mandatory `self.md` gate
- New cross-task review artifact file
- Changing lean/full required file sets

## Constraints

- English docs; bash 3.2 unchanged; FAIL over fake PASS
- Reviewers must not mutate code

## Open Questions

None
