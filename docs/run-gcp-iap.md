# Cloud Run IAP (Feature 003) — no Google Workspace required

Production cutover waits on this path. Feature 002 may still deploy a **public**
URL for experiments (`allow_unauthenticated=true`); that is **not** production.

## What you get

```text
Your Gmail (allowlisted)
  → Google login (IAP, External OAuth brand)
  → Cloud Run media-search
```

The app itself has no login screen — Google’s **Identity-Aware Proxy** is the
gate.

## One-time Console setup (External brand)

Because you do **not** have Google Workspace, use an **External** OAuth consent
screen:

1. GCP Console → **APIs & Services** → **OAuth consent screen**
2. User type: **External**
3. App name e.g. `media-search`, support email = your Gmail
4. Publishing status: **Testing** is fine for a small allowlist  
   (add **Test users** = the same Gmail addresses you will allow)
5. Enable **Cloud Identity-Aware Proxy API** if prompted

Brand / consent is often easier in Console than Terraform for personal
projects; Terraform owns IAM + Cloud Run flags (see `infra/terraform`).

## Terraform (production shape)

```hcl
allow_unauthenticated = false
iap_members = [
  "user:you@gmail.com",
]
image = "REGION-docker.pkg.dev/PROJECT/media-search-repo/media-search:TAG"
```

```bash
cd infra/terraform
terraform apply
```

Effects when `allow_unauthenticated=false`:

- No `allUsers` invoker
- IAP enabled on the Cloud Run service (provider/`gcloud` as available)
- Each `iap_members` entry gets `roles/iap.httpsResourceAccessor`
- IAP service agent gets `roles/run.invoker`

Non-prod experiment (public — do not use for real data):

```hcl
allow_unauthenticated = true
```

## CD (GitHub Actions)

Workflow **deploy-gcp** input `allow_unauthenticated`:

- **`false` (default)** — `--no-allow-unauthenticated` (+ best-effort IAP enable)
- **`true`** — public deploy (prints a warning; non-prod only)

Still configure members via Terraform; CD alone does not add IAP email
allowlist.

## Manual smoke (AC)

1. Open Cloud Run URL in a browser (or Incognito).
2. Sign in with an **allowlisted** Google account → UI should load.
3. Sign in with a **different** account (or no test user) → access denied / 403.
4. Optional: search once after import (same as 002 smoke, but logged in).

Automated CI smoke behind IAP is **out of scope** for 003.

## Common 403 causes

| Symptom | Check |
|---------|--------|
| IAP login then deny | Email not in `iap_members` / not OAuth **Test user** |
| Immediate deny | Still `allUsers` removed but IAP not enabled |
| Works for everyone | `allow_unauthenticated=true` or public invoker left on |

## Related

- Plumbing: `docs/run-gcp.md` (002)
- Spec: `specs/003-iap-access/`
