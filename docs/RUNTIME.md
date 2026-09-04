# Runtime

Portable **capability contract** for executing Project OS agent roles.
The Project OS requires **capabilities**, not product names.

## Principle

```text
Project OS
  → Agent Role Contract (agents/*)
  → Runtime Capability Contract (this file)
  → any compatible runtime (Codex, Claude Code, Cursor, …)
```

Dependency direction is always top-down. The OS never depends on a vendor CLI.

## Required capabilities

A compatible agent runtime MUST be able to:

| Capability | Meaning |
|------------|---------|
| Read repository files | Load specs, rules, agents, docs, code |
| Write permitted repository files | Produce implementation and artifacts in-scope |
| Execute shell commands | Run hooks, scripts, local tools non-interactively when needed |
| Execute verification / tests | Run `./scripts/verify` and project tests when configured |
| Inspect Git state / diff | Support review and pre-merge evidence |
| Consume Agent Role contracts | Read and follow `agents/*.md` |
| Produce review artifacts | Write PASS/FAIL + evidence under `harness/reviews/<feature>/` |

Product names (Codex, Claude Code, Cursor, …) are **examples**, not requirements.

## What the Project OS defines

- Which roles must execute (by profile / loop)
- What each role evaluates
- Convergence and escalation conditions
- Required artifacts and hooks

## What the Project OS does NOT define

- Which AI vendor executes a role
- How agents are spawned / session orchestration
- Vendor-specific CLI flags or IDE click-paths as standard procedure

Non-normative docs MAY say, for example, that an Implementer role may be run by
Codex, Claude Code, Cursor, or another capable runtime. They MUST NOT turn
vendor launch recipes into Project OS workflow.

## Logical independence

| Role | Context rule |
|------|----------------|
| Implementer | Mutates |
| Self Reviewer | **Same** Implementer context allowed |
| Independent Inner (test, code-quality) | **Separate** role invocation/context **required** |
| Outer (product, architecture, security, final) | **Separate** role invocation/context **required** |

Same vendor/runtime across Implementer and Reviewer is allowed.
Forbidden: stay in the Implementer context, only change the role name, and
write independent PASS on your own work.

> Logical independence is contractual, not mechanically attested in v0
> (except presence of `reviewer_role:` on required evaluator artifacts).

Optional `implementer_id` / `reviewer_id` fields MAY appear; mismatch is
**recommended**, never verify-gated in v0.

## Artifact metadata

Required evaluator artifacts (not `analyze.md`) MUST include:

```yaml
---
reviewer_role: <role-name>
---
```

`analyze.md` is a consistency artifact and is exempt from this presence check.

## Vendor CLI boundary

MUST NOT call vendor agent CLIs from:

- `scripts/`
- `hooks/`
- CI workflows (`.github/workflows/`)

Personal Agent OS / human-driven terminals MAY invoke those tools outside the
Project OS tree.

No mechanical grep gate in v0; escalate to an enforcer only if this Failure Mode
appears in practice.

## Relationship to loops

See [`LOOPS.md`](LOOPS.md). Loops classify *when* roles run; this file defines
*what a runtime must be able to do* and independence rules.
