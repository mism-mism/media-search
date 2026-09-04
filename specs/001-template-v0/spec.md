---
id: "001"
status: completed
profile: lean
profile_reason: "Bootstrap exception establishing the template OS; see ADR 0008"
---

# Spec: Template v0 (agentic-engineering-template)

## Problem

Teams adopting AI coding agents lack a portable, vendor-neutral Project OS that
standardizes Spec → Plan → Implement → Verify → Review without shipping a
sample product app or coupling to one person's tooling.

## Goal

Ship a v0 template repository that a project can copy and immediately run the
lean path with honest mechanical verification and independent review artifacts.

## User

Engineers and coding agents working in a newly cloned adopting repository.

## Requirements

1. Constitution, AGENTS.md (canonical), and thin tool shims
2. Spec templates + `new-feature` scaffolding
3. `bootstrap` creates DOMAIN/GLOSSARY stubs
4. `verify` reports PASS / FAIL / SKIP(reason) without lying
5. Review artifact presence gates by profile
6. REFERENCES + ADRs for design lineage
7. No sample application; tech-agnostic enforcer stubs

## Acceptance Criteria

1. `./scripts/bootstrap` succeeds
2. `./scripts/new-feature hello-world` creates `specs/NNN-hello-world/` with expected files
3. Feature directories match the template structure
4. Specs can set `profile: lean` (and `full`) in front matter
5. `./scripts/verify` emits PASS / FAIL / SKIP correctly
6. Missing lean review artifacts are detected for non-completed specs
7. Switching to `full` changes the required artifact set
8. `specs/001-template-v0/` remains with `status: completed`
9. `docs/REFERENCES.md` traces adopted/adapted/rejected ideas
10. Major decisions are recoverable from `docs/adr/`

## Out of Scope

- Pushing/publishing the GitHub template
- Multi-agent orchestration automation
- Stack-specific architecture enforcers with real PASS
- Applying this OS to Laperm / asset server / article AI inside this change

## Constraints

- macOS / Linux; minimal external dependencies; English docs
- Must not depend on a personal Agent OS
- Simple > Clever; no unnecessary abstraction

## Open Questions

None remaining for v0 bootstrap (bootstrap exception; ADR 0008).
