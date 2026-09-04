# AGENTS.md

Canonical agent contract for this repository. Tool-specific files are thin
**vendor-native bridges** only — do not copy policy into them.

Keep this file short. Details live behind the links below.

## Before any work

1. Read [`CONSTITUTION.md`](CONSTITUTION.md).
2. Read the target feature under [`specs/`](specs/) (start with `spec.md`).
3. Check Open Questions in `clarify.md`. If unresolved items affect Domain,
   Constraints, or Acceptance Criteria: **stop** for a human decision.
4. Structure changes → [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
5. Read relevant [`rules/`](rules/).
6. No Acceptance Criteria → no implementation.
7. Drive work through **Inner then Outer loops** ([`docs/LOOPS.md`](docs/LOOPS.md)).
8. Independent evaluators: **separate role invocation** ([`docs/RUNTIME.md`](docs/RUNTIME.md)).
9. Run lifecycle hooks at the boundaries below.
10. Claim done only after Inner+Outer convergence, then `pre-merge` / CI.
11. Do not weaken gates; do not expand scope without approval.

## Loops (required control model)

| Loop | Question |
|------|----------|
| Inner | Did this task/unit converge? |
| Outer | Does the feature satisfy the Spec? |

Implementer **fixes**; Evaluators **evaluate** only. CI **enforces**, it does not revise.
Roles are **vendor-neutral** — any capable runtime may execute them
([`docs/RUNTIME.md`](docs/RUNTIME.md)).
Details: [`docs/LOOPS.md`](docs/LOOPS.md).

## Lifecycle hooks (required)

| Boundary | Command |
|----------|---------|
| Before implementation | `./hooks/pre-implement/check <NNN-slug>` |
| After implementation | `./hooks/post-implement/check <NNN-slug>` |
| Before reviewer handoff | `./hooks/pre-review/check <NNN-slug>` |
| Before merge | `./hooks/pre-merge/check` (**CI enforces**) |

Details: [`hooks/README.md`](hooks/README.md) · CI: [`docs/CI.md`](docs/CI.md)

## Progressive disclosure

| Need | Go to |
|------|--------|
| Principles | [`CONSTITUTION.md`](CONSTITUTION.md) |
| Loops | [`docs/LOOPS.md`](docs/LOOPS.md) |
| Runtime / capabilities | [`docs/RUNTIME.md`](docs/RUNTIME.md) |
| Product intent | [`docs/PRODUCT.md`](docs/PRODUCT.md) |
| Architecture | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| CI / merge gate | [`docs/CI.md`](docs/CI.md) |
| Adoption | [`docs/ADOPTION.md`](docs/ADOPTION.md) |
| Specs | [`specs/README.md`](specs/README.md) |
| Hooks | [`hooks/README.md`](hooks/README.md) |
| Code quality | [`rules/code-quality.md`](rules/code-quality.md) |
| Roles | [`agents/`](agents/) |
| Lineage | [`docs/REFERENCES.md`](docs/REFERENCES.md), [`docs/adr/`](docs/adr/) |

## Authority order

1. Explicit human instruction
2. `CONSTITUTION.md`
3. Active feature `spec.md` (+ `clarify.md` decisions)
4. This `AGENTS.md`
5. `hooks/*`, `rules/*`, `agents/*`
6. `docs/*`
7. README / comments

## Profiles, status, verify

- `profile` = assurance by **risk**
- `status` = lifecycle only — never an exemption for diff-touched gates
- lean Inner: test + code-quality (+ optional self); Outer: product
- full Outer adds architecture, security, final
- Quality axes: Correctness / Understandability / Changeability / Simplicity

## Commands

```bash
./scripts/bootstrap
./scripts/adopt
./scripts/new-feature <slug>
./scripts/verify
FEATURE=<NNN-slug> ./scripts/verify
./hooks/pre-implement/check <NNN-slug>
./hooks/post-implement/check <NNN-slug>
./hooks/pre-review/check <NNN-slug>
./hooks/pre-merge/check
```

## Safety (summary)

No force-push; no unauthorized branch deletion; no production/secrets misuse;
no disabling tests; no weakening gates; no silent scope expansion.
See [`CONSTITUTION.md`](CONSTITUTION.md).
