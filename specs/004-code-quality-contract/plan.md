# Plan: Code Quality Contract

## Architecture

Quality splits Mechanical (verify) vs Judgment (code-quality-reviewer).
Architecture reviewer stays system-structure focused.

## Domain model

N/A (process contract). Quality axes are constitutional terms.

## Interfaces

- `rules/code-quality.md`
- `agents/code-quality-reviewer.md`
- artifact `harness/reviews/<feature>/code-quality.md`

## Dependency direction

Reviewers → rules → constitution. Verify reads artifact presence only.

## Contracts

lean/full required review sets (CLI/docs must match verify).

## Test strategy

FEATURE verify on 001 and 004; layout includes new paths.

## Vertical slice

Constitution + rules + agent + verify + backfill + 004 dogfood reviews.

## Risks

- Lean ceremony +1 artifact
- Reviewer/architecture overlap if boundaries ignored

## Task decomposition

See `tasks.md`.
