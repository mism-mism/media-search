# Glossary

| Term | Definition | Notes |
|------|------------|-------|
| Project OS | Portable repo-level development operating system for agents + humans | This template |
| Constitution | Non-negotiable principles + amendment control | `CONSTITUTION.md` |
| Spec | Source of truth for a feature's intent and acceptance | `specs/NNN-*` |
| Profile | Assurance level by change risk (`lean` / `full`) | Not an effort estimate |
| Harness | Environment for safe/correct agent work (context, reviews, logs, scripts) | Distinct from Agent judgment |
| Hook | Deterministic lifecycle enforcement script under `hooks/*/check` | No LLM inside |
| Adoption | `./scripts/adopt` converts template clone → project OS | Removes dogfood; keeps ADR/REFERENCES |
| Code quality | Correctness, understandability, changeability, simplicity | Not cleverness / abstraction theater; see `rules/code-quality.md` |
| CI | Authoritative merge-time adapter running `pre-merge` | Not a policy engine; see `docs/CI.md` |
| Verify | Scoped deterministic completion checks | Meta vs FEATURE; status ≠ review exemption |
| Inner Loop | Closed task/unit convergence (implement → verify → Inner evaluators → fix) | `docs/LOOPS.md` |
| Outer Loop | Feature/system convergence after Inner; lean product / full + arch/sec/final | `docs/LOOPS.md` |
| Converge | Outer gap → append-only tasks → Inner → Outer again | Not a separate script in v0 |
| Runtime | Capability contract for executing roles; vendor-neutral | `docs/RUNTIME.md` |
| SKIP | Gate not run; must never be reported as PASS | Includes `not_configured` |
| Open Question | Spec-affecting ambiguity reserved for humans | Agents stop |
| Review artifact | Written PASS/FAIL + evidence from an independent reviewer role | Under `harness/reviews/` |
| Shim | Thin tool adapter pointing at `AGENTS.md` | No policy duplication |
| Bootstrap exception | Sole pre-governance dogfood feature `001-template-v0` | ADR 0008 |

Adopting products should extend or replace terms with business language.
