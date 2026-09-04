# ADR 0011: Code quality as a first-class contract

## Context

Architecture, testing, and security were first-class, but everyday
maintainability (readability, naming, accidental complexity, AI over-abstraction)
was only implied. Teams risk equating “Clean Architecture shape” or short diffs
with quality. Lean reviews also omitted an explicit maintainability gate.

## Decision

1. Add Constitution principle: quality = **Correctness, Understandability,
   Changeability, Simplicity**; not cleverness, abstraction density, or
   minimum line count.
2. Add `rules/code-quality.md` with every rule marked
   **Mechanical / Judgment / both** and Enforcer status.
3. Add `agents/code-quality-reviewer.md`; require
   `harness/reviews/<feature>/code-quality.md` on **lean and full**.
4. Mechanical format/lint/type/complexity/dead-code remain
   `SKIP(reason=not_configured)` until stack adapters exist.
5. Clarify Architecture vs Code Quality reviewer boundaries.
6. Retrospectively review features 001–003 under the new contract and persist
   real evidence (N/A with reason where no app code exists).
7. Bump Constitution **0.3.0 → 0.4.0**.

## Alternatives

1. Fold into architecture-reviewer (full only)
2. Grandfather 001–003 without code-quality artifacts
3. Mechanical word-ban lint for `utils`/`helpers`

## Consequences

- Every implementation needs a code-quality review artifact
- Slightly higher lean ceremony; clearer anti-AI-slop signal
- Historical features updated with retrospective review evidence only
- Adopters still must wire mechanical enforcers per stack

## Sync Impact Report

Changed principle(s):

- Code quality four-axis definition
- lean/full require `code-quality.md`
- Mechanical vs Judgment explicit on each rule

Affected surfaces:

| Surface | Sync |
|---------|------|
| `CONSTITUTION.md` | 0.4.0; Code Quality section; review table |
| `rules/code-quality.md` | New |
| `agents/code-quality-reviewer.md` | New |
| `agents/architecture-reviewer.md` | Boundary text |
| `scripts/verify` | required review set + layout + SKIP rows |
| `AGENTS.md` / `docs/ARCHITECTURE.md` / `docs/CI.md` / PR template / specs README | Sync |
| `harness/reviews/001–003/code-quality.md` | Retrospective evidence |
| `specs/004-code-quality-contract/` | Dogfood feature |

Synchronization completed? **yes** (this change set).

## References

- Design grilling (code quality contract)
- `rules/code-quality.md`
- `specs/004-code-quality-contract/`
