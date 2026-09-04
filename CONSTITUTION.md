# Constitution

Version: 0.7.0  
Status: active  
Last amended: 2026-09-05

This document defines non-negotiable principles for repositories that adopt
**agentic-engineering-template**. Local optimization must not override these
principles.

## Purpose

Provide a portable **Project OS** for AI-assisted software development:
Spec-Driven Development, Harness Engineering, Agent Review, Mechanical
Verification, and Human Review — without product-specific application code.

## Failure modes this constitution protects against

| Principle area | Named failure mode |
|----------------|--------------------|
| Spec as source of truth | Ambiguity drift and silent requirement invention |
| Mechanical verification | Trusting unverified agent output |
| Lifecycle hooks | Relying on agent compliance alone at critical boundaries |
| CI merge gate | Merging without authoritative deterministic enforcement |
| Status misuse | Using `completed`/`draft` to skip diff-touched gates |
| Code quality drift | Cleverness / abstraction theater mistaken for quality |
| Template history leak | Shipping template dogfood as the adopting project's history |
| Open-loop delivery | Implement → review treated as one-shot; no convergence definition |
| Vendor/runtime lock-in | Project OS invaded by a specific AI vendor or agent CLI |
| Independent review | Implementer self-confirmation bias |
| Portable Project OS | Coupling to one person's agent tooling |
| Ceremony discipline | Bureaucratic process with no protected failure mode |
| Safety rails | Destructive or unconstrained agent actions |

## 1. Portable Project OS

This repository (and clones) must not depend on any personal Agent OS
(global rules, local orchestrators, private skills). Personal tooling may
optionally adapt *to* this Project OS; the Project OS must not know about
personal tooling.

**Template development history and adopted project history are separate
concerns.** Adoption MUST remove template dogfood artifacts while preserving
the Project OS contracts and their design provenance. See `docs/ADOPTION.md`
and `./scripts/adopt`.

## 2. Spec-Driven Development

- Specs are the source of truth for intended behavior.
- Agents must not invent requirements to fill gaps.
- Ambiguities that affect Domain, Constraints, or Acceptance Criteria become
  Open Questions for humans. Agents stop until decisions are recorded.
- Implementation details (naming helpers, formatting) are not Open Questions.

## 3. Profiles are assurance levels, not effort estimates

Profiles select **guarantee level by change risk**, not by perceived size.

| Profile | When |
|---------|------|
| `lean` | Local behavior change without architecture, security boundary, constitution, or cross-component contract impact |
| `full` | Architecture, security boundary, constitution, external/public contracts, or large domain change |

Architecture or security-boundary features **must** use `full`. Do not invent
ad-hoc “lean + extra reviewer” exception matrices.

### Lean path

Specify → Clarify (if needed) → Plan → Tasks → **pre-implement** → Implement →
**post-implement** → Verify → **pre-review** → Reviews → **pre-merge** / CI → Human

### Full path

Specify → Clarify → Plan → Checklist → Tasks → Analyze → **pre-implement** →
Implement → **post-implement** → Verify → **pre-review** → Reviews → Final →
**pre-merge** / CI → Human

## 4. Feature status vs inspection scope

| Concept | Meaning |
|---------|---------|
| `status` | Feature lifecycle (`draft` / `active` / `completed`) |
| diff | What the current change set touched |
| `profile` | Required assurance level |
| verify | Completeness for a scoped feature |
| pre-merge | Merge eligibility for the change set |
| CI | Authoritative enforcement adapter |

**A feature touched by the current diff MUST NOT be exempted from verification
based on lifecycle status.** Marking `completed` in the same PR does not skip
gates.

### Status meanings

| Status | Meaning |
|--------|---------|
| `draft` | Spec/plan may mature; **implementation merge is forbidden** |
| `active` | Implementation merge permitted |
| `completed` | Historical; excluded from *unrelated* whole-repo scans only |

### Draft exception

`draft` permits a **spec-only** change set: every changed path must be under
`specs/<feature>/**` or `harness/reviews/<feature>/**`. Reviews are not
required. Any other path in that change set → fail (`draft-with-implementation`).

## 5. Agent vs Harness

- **Agent**: who decides what (roles, judgment, planning, implementation, review opinions).
- **Harness**: the environment that keeps agents safe and correct (context, logs,
  review artifacts, hooks, reproducible commands, CI adapter).

Do not conflate planned work with observed completion. Completion requires evidence.

## 6. Mechanical verification first

- Deterministic checks belong in `./scripts/verify` and executable lifecycle hooks.
- Never treat “not checked” as PASS.
- Unconfigured enforcers report `SKIP(reason=not_configured)`.
- Agents must not weaken lint, types, tests, or architecture rules to obtain green verify.

### Verify scope

- `./scripts/verify` — repository global/meta verification only.
- `FEATURE=<NNN-slug> ./scripts/verify` — meta **plus** that feature’s completeness
  (including required reviews for the profile). **Status does not skip reviews.**
- Claiming completion without a feature-scoped verify is invalid.

## 7. Lifecycle hooks (deterministic enforcement)

**Deterministic policy enforcement SHOULD occur at lifecycle boundaries through
executable hooks, rather than relying on agent compliance alone.**

| Surface | Role |
|---------|------|
| CONSTITUTION | Why / invariant principles |
| RULES | What must hold |
| HOOKS | When enforcement happens |
| VERIFY | Whether deterministic requirements hold (for a scope) |
| INNER LOOP | Local implementation convergence |
| OUTER LOOP | Feature / system convergence |
| REVIEW | Judgment-based evaluation inside loops |
| AGENT ROLE | Vendor-neutral role contracts (`agents/*`) |
| RUNTIME | Capability contract for executing roles (`docs/RUNTIME.md`) |
| CI | Authoritative merge-time enforcement (not a loop) |
| HUMAN | Judgment / escalation / acceptance |

Hooks must be **deterministic** (no LLM judgment inside hooks).
Reviewers provide non-deterministic judgment.

v0 required hooks:

- `./hooks/pre-implement/check`
- `./hooks/post-implement/check`
- `./hooks/pre-review/check`
- `./hooks/pre-merge/check`

## 8. Loop engineering (convergence control)

Quality is created by **closed loops**, not one-shot handoffs.

### Inner Loop (task / implementation unit)

Autonomous convergence for a unit of work:

Implement → post-implement → FEATURE verify → Self Review (optional) →
Inner evaluators (test, code-quality) → Fix by **Implementer** until PASS.

**Inner Converged** when FEATURE verify PASS and required Inner evaluator
artifacts PASS (`test`, `code-quality`). Self-review is recommended, not required.

### Outer Loop (feature / system)

After tasks are Inner-converged, Outer evaluators audit the **whole feature**:

- lean Outer: product
- full Outer: product + architecture + security + final
  (final includes cross-task / regression / feature-wide consistency)

**Outer Converged** when required Outer evaluators PASS and there is **no
unresolved gap**.

### Converge (Outer gap protocol)

If Outer evaluation FAILs with a gap:

1. Append new tasks to `tasks.md` (**append-only** — do not rewrite history to hide gaps)
2. Run Inner Loop(s) for those tasks
3. Re-run Outer evaluation

No dedicated converge script/hook in v0. See `docs/LOOPS.md`.

### Roles inside loops

| Role | Mutates? |
|------|----------|
| Implementer | Yes (implement / fix) |
| Evaluator / Reviewer | No (PASS/FAIL + evidence only) |
| CI | No (enforce only) |
| Human | Decides / escalates / accepts |

Reviewers MUST NOT fix code and then self-PASS.

### Human escalation

Inner and Outer Loops SHOULD converge autonomously.
Human escalation is required when ambiguity, high-risk judgment, repeated
non-convergence, conflicting evaluator findings, or final acceptance requires
human authority. Project specs MAY record optional `max_inner_iterations` /
`max_outer_iterations`; the template does not force global defaults.

### CI is not a loop

```text
Loops = quality creation
CI    = quality enforcement
```

CI rejects a false “converged” claim; it does not run generate→revise cycles.

## 9. CI as authoritative merge defense

**CI is the authoritative merge-time enforcement boundary.**

- Hook = agent execution-time boundary defense (contract).
- CI = merge-time authoritative defense (mechanical), by invoking repo
  `./hooks/pre-merge/check` — not by re-implementing policy in YAML.
- CI must not run LLM reviewers, mutate the repository, commit fixes, or approve PRs.
- Required workflow uses no `paths` filters (always starts; internal SKIP is honest).
- Triggers include `pull_request` and `merge_group` (merge queue) plus `push` to
  default branches as **repository health check** (post-hoc — does not rewind a push).
- True merge protection also requires GitHub Rulesets / branch protection with this
  workflow as a **required status check** (see `docs/CI.md`).
- CI is **not** an Inner/Outer Loop (see §8).

## 10. Independent review

- Implementer and Reviewer are separated.
- Reviewers do not edit code by default; they return PASS or FAIL with evidence.
- Required review artifacts must exist for diff-touched features under merge scope
  (except draft spec-only).
- **Self Review** MAY run in the same Implementer context.
- **Independent Inner evaluators** (test, code-quality) and **Outer evaluators**
  MUST run as a **separate role invocation/context** — not by renaming the
  Implementer turn and self-writing PASS. Same vendor/runtime is allowed.
- Logical independence is **contractual** in v0, not mechanically attested
  (except `reviewer_role:` presence on required evaluator artifacts).
- Implementer ≠ reviewer identity fields are **not** mechanically proven in v0.

### Required review artifacts

| Profile | Required artifacts under `harness/reviews/<feature>/` |
|---------|------------------------------------------------------|
| lean | `product.md`, `test.md`, `code-quality.md` |
| full | `product.md`, `test.md`, `code-quality.md`, `architecture.md`, `security.md`, `final.md`, plus `analyze.md` |

## 11. Code quality

Code quality is evaluated by its **correctness, understandability,
changeability, and simplicity**.

Code MUST NOT optimize for cleverness, abstraction density, or minimum line
count at the expense of these qualities. Short code, heavily abstracted code,
or code that merely *resembles* Clean Architecture is not quality by itself.

Detailed and evolvable requirements belong in `rules/code-quality.md`.
Each rule there MUST declare Evaluation as **Mechanical**, **Judgment**, or both.

- Mechanical → `./scripts/verify` (SKIP until configured; never fake PASS)
- Judgment → `code-quality-reviewer` (`code-quality.md` artifact on lean and full)

## 12. Architecture

- SOLID, especially Dependency Inversion.
- Domain must not depend on Infrastructure.
- Frameworks, databases, clouds, and external APIs are details.
- Dependency direction must be explicit.
- Architecture rules that can be automated must appear in `rules/architecture.md` with an Enforcer. Until configured: SKIP, not PASS.

Prefer vertical slices. Avoid speculative abstraction.

## 13. Human vs Agent responsibility

**Human owns:** What, Why, Constraints, Priority, Acceptance, Judgment.

**Agent owns:** Clarify (surface questions), Plan, Implement, Test, Review, Fix.

## 14. Safety — agents must not

- Force-push
- Delete branches without explicit permission
- Modify production resources without explicit permission
- Expose or modify secrets
- Disable tests
- Weaken lint / typecheck / architecture rules to pass verification
- Expand scope without approval

## 15. Ceremony discipline

Every **mandatory** ceremony must protect against a **named failure mode**.
If the failure mode cannot be named, the ceremony is not mandatory in v0.

| Ceremony | Failure mode |
|----------|--------------|
| Clarify / Open Questions | Ambiguity drift |
| Lifecycle hooks | Policy drift at boundaries via agent non-compliance |
| Inner / Outer Loops | Open-loop delivery without defined convergence |
| CI / pre-merge | Merge without authoritative deterministic enforcement |
| Verify | Undetected deterministic regressions |
| Code quality review | Accidental complexity / AI abstraction theater |
| Adoption | Template dogfood leaking into product feature numbering |
| Independent review artifacts | Implementer self-confirmation bias |
| Portable agent runtime | Vendor/runtime lock-in of the Project OS |
| ADR | Loss of architectural decision rationale |
| Constitution + Sync Impact | Principle collapse via local optimization |
| Metrics (non-gating) | Inability to see where harness — not prompts — should improve |

## 16. Dogfooding and change control

This template must use its own workflow for subsequent changes.

| Change class | Path |
|--------------|------|
| trivial | typo / broken link / formatting — short path |
| normal | docs / scripts / ordinary template behavior — lean or better |
| structural | harness / workflow / agents / architecture rules / hooks — lean+ (full when risk warrants) |
| constitutional | `CONSTITUTION.md` — **full + ADR + semver + Sync Impact Report** |

### Structural contract surfaces (always require a feature spec in the change)

Changes to these paths require a corresponding `specs/NNN-*` in the same change set
(unless explicitly listed as spec-exempt in `hooks/pre-merge` / docs):

`CONSTITUTION.md`, `AGENTS.md`, `hooks/**`, `rules/**`, `agents/**`, `harness/**`
(except logs), `scripts/**`, `.github/workflows/**`, `docs/ARCHITECTURE.md`, and
any non-exempt path (including future `src/**`).

### Sync Impact Report (constitutional changes)

Record inside the governing ADR under `## Sync Impact Report`:

1. Changed principle(s)
2. Affected surfaces: `AGENTS.md`, `rules/*`, `agents/*`, `hooks/*`, `scripts/*`, workflows, spec templates
3. Synchronization completed? yes/no with notes

### Bootstrap exception

`specs/001-template-v0/` established governance before these rules existed.
It is the **only** bootstrap exception. No further exceptions.

## 17. Tool instructions

`AGENTS.md` is the canonical agent contract. Tool-specific files are thin
**vendor-native bridges** that point at `AGENTS.md` and must not duplicate policy.
Bridge syntax may follow the tool (`@AGENTS.md` or prose referencing `AGENTS.md`).
Verify only requires an unambiguous reference to `AGENTS.md`.

## 18. Portable agent runtime

**Agent roles and Project OS workflows MUST remain independent of specific AI
vendors and runtimes.**

- The Project OS defines roles, artifacts, hooks, loops, and convergence —
  not which product executes a role.
- Runtimes are admitted by **capabilities**, not product names
  (see `docs/RUNTIME.md`).
- `scripts/`, `hooks/`, and CI MUST NOT invoke vendor agent CLIs
  (`codex`, `claude`, Cursor agent CLIs, etc.). Humans / personal Agent OS may.
- Docs MAY give non-normative examples naming vendors; they MUST NOT standardize
  vendor-specific launch procedures as Project OS workflow.

## Amendment

1. Open a `full` profile spec describing the constitutional change.
2. Draft ADR + Sync Impact Report (in the ADR).
3. Bump constitution semver (MAJOR = incompatible principle change).
4. Synchronize affected surfaces in the same change set.
5. Human acceptance required.
