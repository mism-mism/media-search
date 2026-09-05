# Testing Rules

## Principles

- Prefer tests that lock Acceptance Criteria.
- Failure paths and edge cases matter as much as happy paths.
- Do not disable tests to pass verify.
- Hermetic defaults; opt-in for live external systems.

## Rule table

| Rule | Enforcer | Status |
|------|----------|--------|
| Unit tests | `python3 -m pytest -q` (via `./scripts/verify`) | configured |
| Integration tests | NOT_CONFIGURED | SKIP |
| Acceptance tests | NOT_CONFIGURED | SKIP |

## Adopting projects

Wire real commands into `./scripts/verify`. Until then, SKIP with
`reason=not_configured` is correct.
