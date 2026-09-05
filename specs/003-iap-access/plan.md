# Plan: 003-iap-access

## Approach

After clarify: update Terraform to enable IAP on Cloud Run, remove `allUsers`
invoker, bind IAP + selected principals. Update CD env/IAM. Document operator
runbook. Keep application auth-agnostic unless Q1 selects JWT verification.

## Likely surfaces (pending clarify)

- `infra/terraform` — IAP, IAM bindings, OAuth brand references
- `.github/workflows/deploy-gcp.yml` — drop `--allow-unauthenticated`
- `docs/run-gcp.md` or `docs/run-gcp-iap.md`
- Optional: smoke script with `gcloud` user creds / IAP tunnel

## Non-goals

- Vertex
- Changing 002 product search behavior
