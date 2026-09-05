# Clarify: GCP Deployment

## Ambiguities

001 locked Local-first and deferred concrete GCP services. 002 selects them
now. Product search contract stays unless reopened.

## Questions

| ID | Question | Options | Status |
|----|----------|---------|--------|
| Q1 | 002 slice boundary | A deploy same stack / B +Vertex eval / C Vertex-first | resolved → A |
| Q2 | Compute runtime | A Cloud Run / B GCE / C GKE | resolved → A |
| Q3 | Media object storage | A GCS / B container disk / C Filestore | resolved → A |
| Q4 | Embedding on GCP | A OpenCLIP in runtime / B Vertex / C A+B switch | resolved → A |
| Q5 | Vector + metadata store | A sqlite(+vec) on Run / B Cloud SQL / C Vertex VS | resolved → A |
| Q6 | Preview URLs | A app streams GCS / B signed URL / C public | resolved → A |
| Q7 | Auth for v0 GCP | A none / B IAP / C Identity Platform | resolved → A |
| Q8 | IaC depth | A docs+scripts / B Terraform+CI/CD / C full modules | resolved → B+ |
| Q9 | Semantic gate on GCP | A local only / B +deploy smoke / C full cloud golden | resolved → B |
| Q10 | IaC tool | A Terraform / B Pulumi / C gcloud-only | resolved → A |
| Q11 | CD trigger | A main auto / B workflow_dispatch / C tag only | resolved → B |
| Q12 | Environments | A single / B staging+prod | resolved → A |

## Decisions

| ID | Decision | Decided by | Date |
|----|----------|------------|------|
| D0 | 001 completed; hand off to 002 allowed | Human | 2026-09-05 |
| D1 | 002 = deploy **same** app stack on GCP (Vertex path out of 002) | Human | 2026-09-05 |
| D2 | Compute = **Cloud Run** | Human | 2026-09-05 |
| D3 | Media storage = **GCS** | Human | 2026-09-05 |
| D4 | Embedding = **OpenCLIP in runtime** (001 model family) | Human | 2026-09-05 |
| D5 | Vector/metadata = **sqlite + sqlite-vec** alongside Cloud Run | Human (rec) | 2026-09-05 |
| D6 | Preview = app **streams from GCS** via `/media` | Human (rec) | 2026-09-05 |
| D7 | Auth v0 = **none** (IAM/network experiment; harden later) | Human (rec) | 2026-09-05 |
| D8 | **IaC + CI/CD first-class** | Human | 2026-09-05 |
| D9 | Semantic: local `semantic-real` Required + **deployed URL smoke** | Human (rec) | 2026-09-05 |
| D10 | IaC = **Terraform** (minimal: AR, GCS, Cloud Run, IAM, SA) | Human (rec) | 2026-09-05 |
| D11 | CD = GitHub Actions **`workflow_dispatch`** → build/push/deploy | Human (rec) | 2026-09-05 |
| D12 | **Single** GCP project / env for 002 | Human (rec) | 2026-09-05 |
| D13 | Shared understanding locked for 002 service map | Human | 2026-09-05 |

## Unresolved items

- None
