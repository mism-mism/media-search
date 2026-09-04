---
id: "007"
status: completed
profile: full
profile_reason: "Constitutional: vendor/runtime independence of Project OS roles"
---

# Spec: Portable Agent Runtime

## Problem

Project OS workflows and roles can be written (or automated) as if they belong
to one coding-agent vendor, so portability dies when that product churns.

## Goal

Lock a **vendor-neutral** boundary: roles + capabilities in-repo; vendor bridges
thin and native; no vendor agent CLIs in scripts/hooks/CI; independent evaluator
invocation as contract (with `reviewer_role:` presence check only).

## User

Engineers and agents using this Project OS across Codex / Claude Code / Cursor /
future runtimes; template maintainers.

## Requirements

1. Constitution 0.7.0 with Portable agent runtime section + Sync Impact ADR
2. `docs/RUNTIME.md` capability + independence contract
3. LOOPS / AGENTS / ARCHITECTURE / README synced
4. Claude + Cursor shims use `@AGENTS.md`; Gemini/Copilot remain thin prose
5. Independent Inner/Outer evaluators require separate invocation; Self same OK
6. FEATURE verify checks `reviewer_role:` presence (not analyze; not identity)
7. No vendor agent CLI wrappers under scripts/hooks/CI (docs-only ban in v0)
8. `scripts/adopt` EXPECTED includes `007-portable-agent-runtime`

## Acceptance Criteria

1. Constitution Version is 0.7.0; §18 (or equivalent) states vendor independence
2. `docs/RUNTIME.md` exists with required capabilities and independence rules
3. ADR 0014 exists with Sync Impact
4. CLAUDE.md and Cursor rule reference `@AGENTS.md`
5. Shim verify still PASSes (unambiguous `AGENTS.md` reference)
6. FEATURE verify fails without `reviewer_role:` on required evaluator artifacts
7. `scripts/adopt` lists `007-portable-agent-runtime`
8. Full review artifacts for 007 exist with `reviewer_role:`
9. No `scripts/*` vendor agent runner added

## Out of Scope

- Vendor CLI grep gate in verify
- `implementer_id` / `reviewer_id` mismatch gate
- Cross-vendor Generator≠Evaluator as MUST
- Personal Agent OS / vendor launch procedures as OS standard
- `./scripts/loop` or runtime orchestrator

## Constraints

- English docs; bash 3.2; FAIL over fake PASS
- Contract portable; bridges vendor-native

## Open Questions

None
