---
id: "003"
status: active
profile: full
profile_reason: "Access control / IAM / IAP for internet-facing Cloud Run — security-sensitive."
---

# Spec: Cloud Run IAP Access Control

## Problem

Feature 002 deploys media-search to Cloud Run **without authentication** (v0).
A public URL allows search, import, and media access, and can drive cost abuse.
This is unacceptable for **production**.

The operator does **not** have Google Workspace, so IAP must work with
**personal Google accounts** (External OAuth brand + email allowlist).

## Goal

Put **Identity-Aware Proxy (IAP)** in front of the Cloud Run service so only
allowlisted Google identities can reach the app — **before** any production
cutover.

```text
User (Google account, e.g. Gmail)
    → IAP (External OAuth brand)
    → Cloud Run (media-search)
    → GCS / sqlite-vec / OpenCLIP
```

002 plumbing stays; this feature **removes anonymous invoker** (for prod) and
documents the operator access model.

## User

GCP project operators who grant/revoke access by editing an email allowlist
(Terraform variable / IAM members).

## Requirements

- R1. Production-intended path must **not** grant `roles/run.invoker` to
  `allUsers`.
- R2. Access via **IAP attached to Cloud Run** (HTTPS; no HTTPS LB required in
  003).
- R3. Allowed principals = Terraform-configured list of
  `user:<email>` (and optional `serviceAccount:` for tooling) — **not** a
  Workspace Google Group.
- R4. OAuth consent brand = **External**; document test-user / verification
  caveats for personal Gmail.
- R5. Docs cover: enable IAP, brand, add emails, common 403 failures, browser
  smoke.
- R6. CD/deploy must not silently re-introduce public invoker when IAP mode is
  on.
- R7. Domain / Application remain **auth-agnostic** (edge IAP only).
- R8. Terraform supports `allow_unauthenticated` (or equivalent) for **non-prod
  experiments**; **production docs/tfvars require IAP** (anonymous off).
- R9. Explicit: **production cutover only after this Feature converges**.

## Acceptance Criteria

- AC1. Clarify decisions locked (no open OQ) — done in clarify.md.
- AC2. Terraform (+ CD as needed) can provision IAP + email allowlist such that
  anonymous access fails and an allowlisted Google account succeeds in browser.
- AC3. Docs (`docs/run-gcp-iap.md` and/or updates to `run-gcp.md`) explain
  grant/revoke and manual smoke behind IAP.
- AC4. Full-profile reviews PASS.
- AC5. PRODUCT / runbooks state production cutover waits on 003.

## Out of Scope

- Vertex embeddings / Vector Search
- Google Workspace / Internal brand
- App-level IAP JWT verification
- HTTPS Load Balancer in front of Cloud Run
- Automated IAP smoke in CI (manual browser is enough for 003)
- Rewriting Domain for auth
- Changing 001 local-first developer loop

## Constraints

- Depends on 002 GCP deploy surface (Cloud Run + GCS).
- Prefer Google-documented IAP-for-Cloud-Run with External brand.
- No long-lived secrets in git.

## Open Questions

None — see [`clarify.md`](clarify.md).
