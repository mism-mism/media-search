---
id: "013"
status: completed
profile: lean
profile_reason: "Billing/ops config; alert-only; no product Domain change"
---

# Spec: GCP cost controls

## Problem

Cloud spend can grow unnoticed (min-instances, Import Jobs, GCS, BQ).

## Goal

Monthly **USD 50** budget with email alerts at 50/90/100% for the media-search
project. Alert-only — no hard billing disable (D1/D6).

## User

Project owner paying the GCP bill.

## Requirements

- R1. Monthly budget USD 50 (D2).
- R2. Thresholds 50% / 90% / 100% (D3).
- R3. Email `mishima0304@gmail.com` (D4).
- R4. Document that budgets do **not** hard-stop spend (D1).
- R5. Terraform reproducible; billing account via tfvars (not invent secrets).
- R6. Note cost drivers in ops docs.

## Acceptance Criteria

- AC1. Clarify Round 1 locked (D0–D5).
- AC2. `google_billing_budget` (or equivalent) applied / documented for project.
- AC3. `docs/run-gcp.md` explains budget + how to change amount/email.
- AC4. No billing-disable automation.
- AC5. Lean reviews PASS.

## Out of Scope

- Hard disable billing / FinOps multi-project
- Changing Import or embedder
- Slack Pub/Sub (later)

## Constraints

- Billing Budgets API + Monitoring notification channel
- Domain free of GCP SDKs (Terraform/docs only)

## Open Questions

None.
