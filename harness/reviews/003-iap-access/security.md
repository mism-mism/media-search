---
reviewer_role: security-reviewer
reviewer_id: security-review-subagent
---

# Security review: 003-iap-access

## Verdict: PASS

- Production path removes `allUsers` when `allow_unauthenticated=false`
- Allowlist via `user:` emails; External brand documented for non-Workspace
- Non-prod public flag is explicit and warned in CD
- No secrets committed; tfvars example uses placeholders
- App does not implement custom auth (attack surface stays at IAP)

## Residual

- External OAuth “Testing” mode test-user limits — operator must maintain list
- Confirm IAP enabled on service after first apply (Console/`gcloud beta`)
