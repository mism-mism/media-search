---
reviewer_role: security-reviewer
feature: 004-vertex-eval
verdict: PASS
---

# Security review: 004

Eval uses ADC; no secrets committed. Production Cloud Run IAP / default
embedder not switched. Vertex API enablement is project-scoped and does not
re-open anonymous invoker.
