---
reviewer_role: security-reviewer
---

# Security review: 005-template-adoption

**Verdict:** PASS

## Evidence

- Destructive paths limited to known feature dirs under specs/harness
- Unknown features refuse deletion (fail closed)
- No credentials/network; read-only GitHub settings remain manual
- Double-adopt does not re-wipe arbitrarily
