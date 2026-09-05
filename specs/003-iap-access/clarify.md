# Clarify: Cloud Run IAP Access Control

## Ambiguities

002 chose auth=none for v0. Production requires IAP; configuration details
must be locked before Terraform/CD changes.

## Questions

| ID | Question | Status |
|----|----------|--------|
| Q1 | IAP placement | open — edge IAP only vs app verifies IAP JWT too |
| Q2 | Allowed principals | open — Google Group vs individual users vs both |
| Q3 | OAuth brand | open — Internal (Workspace) vs External |
| Q4 | Dev/staging exception | open — keep public invoker flag for non-prod? |
| Q5 | IAP on load balancer vs Cloud Run IAP | open — recommended Cloud Run IAP |
| Q6 | Service account invokers (CD smoke) | open — how smoke works behind IAP |
| Q7 | Workspace / org requirement | open — Google Workspace required? |

## Decisions

| ID | Decision | Decided by | Date |
|----|----------|------------|------|
| D0 | IAP is a **separate** Feature/PR/workspace from 002 | Human | 2026-09-05 |
| D1 | Production cutover **only after** IAP converges | Human | 2026-09-05 |
| D2 | 002 PR remains unauthenticated v0 plumbing (no scope change there) | Human | 2026-09-05 |

## Unresolved items

- Q1–Q7 (blocking for AC1 / implementation)
