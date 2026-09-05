# Cloud Run IAP (Feature 003) — no Google Workspace required

Feature **003 is completed** for this project: production-intended Cloud Run
is behind IAP with a Gmail allowlist. Feature 002 may still use a **public**
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

Personal projects (no Organization) **cannot** rely on Google-managed OAuth
alone. You need External consent + a **custom Web OAuth client**.

1. GCP Console → **Google Auth Platform / OAuth consent**  
   - Audience: **External**  
   - Publishing: **Testing** is fine  
   - **Test users** = the same Gmails as `iap_members`
2. Enable **Cloud Identity-Aware Proxy API** if prompted
3. Cloud Run → `media-search` → **Security** → **Identity-Aware Proxy** ON  
   (first enable in a no-Org project may show *Empty Google Account OAuth
   client ID(s)/secret(s)* — fix with the custom client below)
4. Create OAuth client: **Web application**  
   [Clients](https://console.cloud.google.com/auth/clients)
5. After create, edit **Authorized redirect URIs** and add **exactly**:

```text
https://iap.googleapis.com/v1/oauth/clientIds/YOUR_CLIENT_ID:handleRedirect
```

6. Apply client to IAP (fish):

```fish
printf '%s\n' \
  'access_settings:' \
  '  oauth_settings:' \
  '    client_id: "YOUR_CLIENT_ID"' \
  '    client_secret: "YOUR_CLIENT_SECRET"' \
  > /tmp/iap_settings.yaml

gcloud iap settings set /tmp/iap_settings.yaml --project=YOUR_PROJECT
rm /tmp/iap_settings.yaml
```

Do **not** commit client secrets.

## Terraform (production shape)

```hcl
allow_unauthenticated = false
iap_members = [
  "user:you@gmail.com",
]
image = "REGION-docker.pkg.dev/PROJECT/media-search-repo/media-search@sha256:…"
```

```bash
cd infra/terraform
# mise use terraform@1.16.1   # if needed
terraform apply
```

Then enable IAP on the service if needed:

```bash
gcloud run services update media-search --region=REGION --iap --quiet
```

Effects when `allow_unauthenticated=false`:

- No `allUsers` invoker
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
3. Sign in with a **different** account (or no test user) → access denied.
4. Anonymous `curl` → **302** (IAP login) or **403** — not a 200 JSON health.

Automated CI smoke behind IAP is **out of scope** for 003.

## Common failures

| Symptom | Check |
|---------|--------|
| Empty OAuth client ID(s)/secret(s) | Create Web client + `gcloud iap settings set` |
| `redirect_uri_mismatch` | Redirect URI must use the **same** Client ID as IAP settings, exact string above |
| IAP login then deny | Email not in `iap_members` / not OAuth **Test user** |
| Immediate deny, no Google UI | `allUsers` removed but IAP/OAuth not configured |
| Works for everyone | `allow_unauthenticated=true` or public invoker left on |

## Related

- Plumbing: [`docs/run-gcp.md`](run-gcp.md) (002)
- Menu: [`README.md`](../README.md)
- Spec: [`specs/003-iap-access/`](../specs/003-iap-access/)
