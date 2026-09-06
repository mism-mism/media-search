# Research: 013 GCP cost controls

Date: 2026-09-06

## Live budget

| Field | Value |
|-------|--------|
| Billing account | `01A7CD-8FAFFE-6D530B` (account currency JPY; budget amount **USD**) |
| Budget | `media-search-monthly-50usd` |
| Filter | project `laperm-507708` (`142769597956`) |
| Amount | **50 USD** / MONTH |
| Thresholds | 50% / 90% / 100% CURRENT_SPEND |
| Channel | `projects/laperm-507708/notificationChannels/1755512545472650656` → `mishima0304@gmail.com` |

Created via `gcloud billing budgets` (local Terraform binary not available in this
environment). Equivalent resources are in `infra/terraform/main.tf` for future
`terraform apply` / import.

## Semantics

**Alert only** — exceeding 100% does **not** stop Cloud Run or disable billing.

## Operator action

Verify the Monitoring email channel if Google sent a confirmation link.
