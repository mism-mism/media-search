# Plan: Template v0

## Architecture

Process/harness OS: Constitution → AGENTS → specs → agents/rules → harness → scripts.
No application domain layers in this repository.

## Domain model

N/A (template meta-product). Adopting repos fill DOMAIN/GLOSSARY via bootstrap.

## Interfaces

- `./scripts/bootstrap`
- `./scripts/new-feature <slug>`
- `./scripts/verify`

## Dependency direction

Scripts depend on layout conventions only. Tool shims depend on AGENTS.md.
Verify may read specs front matter and harness/reviews; it must not invent PASS.

## Contracts

CLI contracts for the three scripts above (argv, exit codes, stdout status lines).
No external network API.

## Test strategy

Manual executable acceptance criteria in README / this spec; verify self-checks
meta gates; create temporary feature to assert review-gate behavior.

## Vertical slice

One completed lean feature record (`001-template-v0`) plus working scripts.

## Risks

- Many SKIPs may be misread as success → document honesty rules
- Empty review files could rubber-stamp → v1 quality checks

## Task decomposition

See `tasks.md`.
