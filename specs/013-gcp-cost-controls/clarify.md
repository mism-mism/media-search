# Clarify: GCP cost controls

## Ambiguities

Want a **cost ceiling** so media-search on `laperm-507708` cannot run away
(min-instances=1, Import Job 4CPU/16Gi, GCS, optional BQ eval).

Important GCP fact: **Billing budgets alert by default; they do not hard-stop
charges.** Hard stop usually means “disable billing on the project” (service
outage) or custom automation. Soft controls = budget alerts + instance/API caps.

## Questions

| ID | Question | Options | Status |
|----|----------|---------|--------|
| Q1 | Scope of 013 | A **Budget alerts only (Terraform + docs)** / B A + tighten quotas / C A + auto disable billing | resolved → **A** |
| Q2 | Monthly budget amount (USD) | A **50** / B 100 / C 200 / D other | resolved → **A (50)** |
| Q3 | Alert thresholds | A **50% / 90% / 100%** / B 80/100 / C custom | resolved → **A** |
| Q4 | Notify how | A **email** / B Pub/Sub→Slack / C both | resolved → **A** |
| Q5 | Notify email(s) | | resolved → **mishima0304@gmail.com** |
| Q6 | Hard stop at budget | A **No** (alert only) / B disable billing / C scale-to-zero script later | resolved → **A** |
| Q7 | Profile | A **lean** / B full | resolved → **A** |

## Decisions

| ID | Decision | Decided by | Date |
|----|----------|------------|------|
| D0 | 013 = GCP **cost controls** for media-search | Human | 2026-09-06 |
| D1 | Budget alerts only (Terraform + docs); no hard disable billing | Human | 2026-09-06 |
| D2 | Monthly budget **USD 50** | Human | 2026-09-06 |
| D3 | Thresholds **50% / 90% / 100%** of current spend vs budget | Human | 2026-09-06 |
| D4 | Notify by **email** to `mishima0304@gmail.com` | Human | 2026-09-06 |
| D5 | profile = **lean** | Human | 2026-09-06 |

## Unresolved items

None for Domain / Constraints / Acceptance Criteria.
