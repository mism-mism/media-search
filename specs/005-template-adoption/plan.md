# Plan: Template Adoption

## Architecture

Adoption is a one-shot initializer: Template clone → Project OS without dogfood.
Provenance stays in ADR/REFERENCES; feature numbering resets via empty `specs/NNN-*`.

## Domain model

N/A (process). “Dogfood feature” = entry in fixed list in `scripts/adopt`.

## Interfaces

```bash
./scripts/adopt
```

## Dependency direction

adopt → filesystem + `./scripts/verify`. No GitHub API.

## Contracts

Fixed dogfood list must be updated when template adds dogfood features.
Unknown `NNN-*` → non-zero exit.

## Test strategy

Temp directory copy: adopt once (removes dogfood), adopt twice (NO-OP), inject
unknown feature → FAIL.

## Vertical slice

Script + ADOPTION.md + editor/git attrs + Constitution/ADR + verify tolerance
for absent 001.

## Risks

- Maintainers forget to extend EXPECTED list
- Running adopt on a busy product repo with only expected names would delete them
  (mitigation: document fresh-clone-only; unknown FAIL)

## Task decomposition

See `tasks.md`.
