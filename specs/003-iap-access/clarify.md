# Clarify: Cloud Run IAP Access Control

## Ambiguities

002 chose auth=none for v0. Production requires IAP; configuration details
must be locked before Terraform/CD changes.

## Questions

| ID | Question | Options | Status |
|----|----------|---------|--------|
| Q1 | App verifies IAP JWT? | A edge-only / B app verifies JWT | resolved → A |
| Q2 | Allowed principals | A Google Group / B users / C both | resolved → A |
| Q3 | OAuth brand | A Internal / B External | resolved → A |
| Q4 | Non-prod exception | A always IAP / B flag for public dev | resolved → B |
| Q5 | IAP attachment | A Cloud Run IAP / B HTTPS LB + IAP | open |
| Q6 | Smoke behind IAP | A gcloud user browser / B SA + IAP tunnel / C skip automated | open |
| Q7 | Google Workspace required? | A yes (Internal brand) / B allow without | open (likely A given Q3) |

## Decisions

| ID | Decision | Decided by | Date |
|----|----------|------------|------|
| D0 | IAP is a **separate** Feature/PR/workspace from 002 | Human | 2026-09-05 |
| D1 | Production cutover **only after** IAP converges | Human | 2026-09-05 |
| D2 | 002 PR remains unauthenticated v0 plumbing | Human | 2026-09-05 |
| D3 | **Edge IAP only** — app stays auth-agnostic (no IAP JWT check in app) | Human | 2026-09-05 |
| D4 | Allowlist via **one Google Group** | Human | 2026-09-05 |
| D5 | OAuth brand **Internal** (Workspace) | Human | 2026-09-05 |
| D6 | Terraform flag: non-prod may allow unauthenticated; **prod = IAP required** | Human | 2026-09-05 |

## Unresolved items

- Q5–Q7 (blocking for plan/Terraform shape)
