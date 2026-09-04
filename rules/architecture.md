# Architecture Rules

Encode rules that adopting projects will enforce mechanically.
Until an Enforcer command exists, verify must **SKIP**, never PASS.

## Rule table

| Rule | Enforcer | Status |
|------|----------|--------|
| Domain must not depend on Infrastructure | NOT_CONFIGURED | SKIP |
| Dependency direction matches declared layers | NOT_CONFIGURED | SKIP |
| External SDKs confined to adapter/infrastructure boundaries | NOT_CONFIGURED | SKIP |

## How to configure (adopting projects)

1. Choose a mechanism (import linter, structural tests, custom script).
2. Replace `NOT_CONFIGURED` with the command under `scripts/` or package scripts.
3. Wire the command into `./scripts/verify` (and/or lifecycle hooks as needed).
4. Document the layer model in `docs/ARCHITECTURE.md`.

## Template repository note

This template has no application packages; architecture enforcers intentionally
remain `not_configured` so verify stays honest.
