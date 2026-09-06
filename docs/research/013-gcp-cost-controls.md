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
| Channel | Monitoring email → `Mishima0304@gmail.com` (+ Billing Account Admin default recipients) |

Created via `gcloud billing budgets`. Equivalent Terraform in `infra/terraform/main.tf`.

## Semantics

**Alert only** — exceeding 100% does **not** stop Cloud Run or disable billing.

## Operator action

1. Check Gmail **inbox + spam/プロモーション** for “Google Cloud Monitoring” /
   verification code.
2. If a code arrives, verify the channel in Cloud Console → Monitoring →
   Alerting → Notification channels.
3. Billing Account Admin (`Mishima0304@gmail.com`) also receives budget emails
   via default IAM recipients (no channel verify required for that path).
