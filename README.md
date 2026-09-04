# agentic-engineering-template

Portable **Project OS** for AI-assisted software engineering.
Standardizes Spec-Driven Development, Harness Engineering, Agent Review,
Mechanical Verification, and Human Review — without shipping a product app.

## Why this exists

Agents are fast and unreliable as sole judges of correctness. This template
makes specs the source of truth, verification honest, hooks enforceable, and
review independent — with **closed Inner/Outer loops** defining when work has
converged.

## Core philosophy

- Specs over vibes; Open Questions go to humans
- Profiles select **assurance by risk** (`lean` / `full`), not estimated effort
- `SKIP` is never `PASS`
- Hooks = deterministic boundary enforcement; Review = judgment
- Loops = quality **creation**; CI = quality **enforcement**
- Every mandatory ceremony protects a **named failure mode**
- Portable Project OS: no dependency on anyone’s personal Agent OS
- Roles are vendor-neutral; runtimes admit by **capabilities** (`docs/RUNTIME.md`)

## Architecture

```text
CONSTITUTION → RULES → HOOKS → VERIFY → LOOPS → ROLES → RUNTIME → (any capable agent)
                                      ↑
                               specs/ + AGENTS.md
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/LOOPS.md`](docs/LOOPS.md),
[`docs/RUNTIME.md`](docs/RUNTIME.md), and [`hooks/README.md`](hooks/README.md).

## Human vs Agent

| Human | Agent |
|-------|--------|
| What / Why / Constraints / Priority / Acceptance / Judgment | Clarify / Plan / Implement / Inner+Outer loops / Fix |

## Standard workflow

**Lean:** Specify → Clarify? → Plan → Tasks → pre-implement → Implement → **Inner Loop**
(test + code-quality) → **Outer Loop** (product) → Converge if needed → pre-merge → Human

**Full:** + Checklist; Outer adds architecture, security, final (and forced for
architecture/security/constitution)

Details: [`docs/LOOPS.md`](docs/LOOPS.md).

## Starting a new project (from this template)

```bash
# after GitHub "Use this template" + clone:
./scripts/adopt
# edit docs/PRODUCT.md DOMAIN.md GLOSSARY.md
# configure GitHub settings: docs/ADOPTION.md
./scripts/new-feature <slug>   # → specs/001-<slug>/
```

## Starting a new feature (inside an adopted project)

```bash
./scripts/bootstrap
./scripts/new-feature asset-search
./hooks/pre-implement/check 00N-asset-search
```

## Verification

```bash
./scripts/verify
FEATURE=00N-slug ./scripts/verify
./hooks/pre-merge/check
```

CI is a thin adapter that runs `pre-merge` (see [`docs/CI.md`](docs/CI.md)).
Configure the workflow as a **required status check** for real merge protection.

## Review flow

Implementer mutates; evaluators evaluate only. Artifacts under
`harness/reviews/<feature>/`. Feature-scoped verify / pre-merge enforce presence
by profile (lean Inner: test + code-quality; lean Outer: product).

## References

[`docs/REFERENCES.md`](docs/REFERENCES.md) · [`docs/adr/`](docs/adr/) ·
[`docs/LOOPS.md`](docs/LOOPS.md)

## Current limitations (v0)

- Stack enforcers intentionally `not_configured`
- Review quality not CI-judged; evaluator identity independence not mechanically proven
- No `./scripts/loop` runner (contract-only Loop Engineering)
- Vendor agent CLI ban is contractual (no grep gate yet)
- Native Claude/Git hook configs not shipped
- Rulesets must be configured by adopters (documented in `docs/CI.md`)
- Worktree automation not included
