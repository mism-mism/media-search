# Clarify: Cloud Run IAP Access Control

## Ambiguities

002 chose auth=none for v0. Production requires IAP. Operator has **no Google
Workspace** — Internal OAuth brand is unavailable; use External + email
allowlist.

## Questions

| ID | Question | Options | Status |
|----|----------|---------|--------|
| Q1 | App verifies IAP JWT? | A edge-only / B app verifies JWT | resolved → A |
| Q2 | Allowed principals | A Workspace Group / B email allowlist / C both | resolved → **B** (no Workspace) |
| Q3 | OAuth brand | A Internal / B External | resolved → **B** |
| Q4 | Non-prod exception | A always IAP / B flag for public dev | resolved → B |
| Q5 | IAP attachment | A Cloud Run IAP / B HTTPS LB + IAP | resolved → A |
| Q6 | Smoke behind IAP | A browser manual / B SA automation / C skip | resolved → A |
| Q7 | Google Workspace required? | A yes / B no | resolved → **B** |

## Decisions

| ID | Decision | Decided by | Date |
|----|----------|------------|------|
| D0 | IAP is a **separate** Feature/PR/workspace from 002 | Human | 2026-09-05 |
| D1 | Production cutover **only after** IAP converges | Human | 2026-09-05 |
| D2 | 002 PR remains unauthenticated v0 plumbing | Human | 2026-09-05 |
| D3 | **Edge IAP only** — app stays auth-agnostic | Human | 2026-09-05 |
| D4 | Allowlist = **Google account emails** (Terraform `iap_members` / `user:…`) — not Workspace Group | Human | 2026-09-05 |
| D5 | ~~Internal brand~~ superseded by D8 | — | — |
| D6 | Terraform flag: non-prod may allow unauthenticated; **prod = IAP required** | Human | 2026-09-05 |
| D7 | Operator has **no Google Workspace** | Human | 2026-09-05 |
| D8 | OAuth consent brand = **External**; personal Gmail OK (test users / allowlist) | Human | 2026-09-05 |
| D9 | Attach IAP to **Cloud Run directly** (no HTTPS LB in 003) | Human (rec) | 2026-09-05 |
| D10 | Smoke = **manual browser** login against Cloud Run URL; document steps | Human (rec) | 2026-09-05 |
| D11 | Shared understanding locked for 003 IAP config | Human | 2026-09-05 |

## Unresolved items

- None
