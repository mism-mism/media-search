---
id: "003"
status: draft
profile: full
profile_reason: "Access control / IAM / IAP for internet-facing Cloud Run — security-sensitive."
---

# Spec: Cloud Run IAP Access Control

## Problem

Feature 002 deploys media-search to Cloud Run **without authentication** (v0).
A public URL allows search, import, and media access, and can drive cost abuse.
This is unacceptable for **production**.

## Goal

Put **Identity-Aware Proxy (IAP)** in front of the Cloud Run service so only
approved Google identities (users/groups) can reach the app — **before** any
production cutover.

```text
User (Google account)
    → IAP
    → Cloud Run (media-search)
    → GCS / sqlite-vec / OpenCLIP
```

002 plumbing stays; this feature **removes anonymous invoker** and documents
the operator access model.

## User

GCP project operators who grant/revoke access via Google Group (preferred) or
individual accounts.

## Requirements

- R1. Cloud Run must **not** grant `roles/run.invoker` to `allUsers` in the
  production-intended Terraform/CD path.
- R2. Access is via **IAP** for the Cloud Run service (HTTPS).
- R3. Allowed principals are configurable (Terraform variable / documented
  IAM) — prefer a **Google Group**.
- R4. Docs cover: enable IAP, OAuth brand/consent, grant users, common 403
  failures.
- R5. CD/deploy path remains `workflow_dispatch`; must not re-introduce public
  invoker.
- R6. Local (001) and unauthenticated **dev** paths may remain, but must be
  clearly separated from “production” docs/gates.
- R7. Domain / Application still have **no** GCP auth SDK requirement for
  request handling (IAP terminates at Google edge; app may stay auth-agnostic
  in v0 unless clarify selects app-level checks).

## Acceptance Criteria

- AC1. Spec/clarify lock IAP configuration decisions (brand, principals,
  app-level vs edge-only).
- AC2. Terraform (and CD if needed) provision IAP + IAM such that anonymous
  access fails; allowed identity succeeds.
- AC3. `docs/run-gcp.md` (or `docs/run-gcp-iap.md`) explains grant/revoke and
  smoke behind IAP.
- AC4. Security + architecture reviews PASS (full profile).
- AC5. Explicit statement: **production cutover only after this feature
  converges**.

## Out of Scope

- Vertex embeddings / Vector Search (→ later issue)
- End-user product accounts (Firebase/Identity Platform) beyond IAP Google
  identities
- Rewriting Domain for auth
- Changing 001 local-first developer loop

## Constraints

- Depends on 002 GCP deploy surface (Cloud Run + GCS).
- Prefer Google-documented IAP-for-Cloud-Run pattern.
- No long-lived secrets in git.

## Open Questions

See [`clarify.md`](clarify.md) — **blocking** until human decisions.
