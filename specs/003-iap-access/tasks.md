# Tasks: 003-iap-access

## T000 — Clarify

- [x] Resolve OQ; status active; no Workspace / External / email allowlist
- AC: AC1, AC5

## T001 — Terraform IAP + IAM

- [x] `allow_unauthenticated` / `iap_members` / remove public invoker when false
- [x] IAP invoker SA + httpsResourceAccessor members
- [x] Example tfvars (prod vs non-prod)
- AC: AC2

## T002 — CD alignment

- [x] deploy-gcp: `allow_unauthenticated` input; default false; no silent public prod
- AC: AC2

## T003 — Docs + manual smoke

- [x] `docs/run-gcp-iap.md` + production note in `run-gcp.md`
- AC: AC3

## T004 — Outer reviews (full)

- [x] reviews written
- AC: AC4, AC5
