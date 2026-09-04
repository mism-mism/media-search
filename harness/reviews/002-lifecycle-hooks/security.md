---
reviewer_role: security-reviewer
---

# Security review: 002-lifecycle-hooks

**Verdict:** PASS

## Evidence

- Hooks are local bash; no network calls; no secret handling added
- Deterministic checks only (no LLM prompt injection surface inside hooks)
- Diff/path parsing does not execute file contents
- Safety list in Constitution unchanged in intent

## Notes

Secret scanning remains `not_configured` (honest SKIP).
