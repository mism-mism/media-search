---
reviewer_role: security-reviewer
reviewer_id: security-review-subagent
---

# Security review: 002-gcp-deployment

## Verdict

**PASS** — Prior GCS media-key path escape is mitigated (`_safe_key` + materialize
`relative_to`); secrets/WIF/public-v0/`terraform.tfvars` checks remain clean.

## Scope checked

| Area | Result |
|------|--------|
| Secrets in repo | PASS |
| Public Cloud Run documented as v0 | PASS |
| WIF preferred (no long-lived JSON key in CD) | PASS |
| Path traversal on media keys | PASS (re-check after fix) |
| `terraform.tfvars` gitignored | PASS |
| Authn/authz | Intentionally absent (spec R11 / D7); documented |
| Agent safety / committed credentials | PASS |

## Evidence

### Secrets in repo — PASS

- No tracked `.env`, `*.pem`, `*.key`, `terraform.tfvars`, or service-account JSON.
- `infra/terraform/terraform.tfvars.example` is placeholder comments only.
- CD references GitHub secrets by name only
  (`GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT`).
- `rules/security.md`: secret scanning `NOT_CONFIGURED` → process SKIP (harness).

### Public Cloud Run as v0 — PASS

| Location | Evidence |
|----------|----------|
| `docs/run-gcp.md` | `Auth \| none (v0; --allow-unauthenticated)` |
| `specs/002-gcp-deployment/spec.md` R11 | Auth none for v0 |
| `infra/terraform/main.tf` | `member = "allUsers"` on `roles/run.invoker` |
| `.github/workflows/deploy-gcp.yml` | `--allow-unauthenticated` |

### WIF preferred — PASS

- `google-github-actions/auth@v2` with workload identity provider + SA email only.
- No `credentials_json` / key file in workflow.
- Docs: “prefer over JSON keys”.

### `terraform.tfvars` gitignored — PASS

`.gitignore`: `infra/terraform/terraform.tfvars` (confirmed via `git check-ignore -v`).

### Path traversal on media keys — PASS (fixed)

**GCS (`gcs_media_storage.py`):**

1. `_safe_key` normalizes separators, drops empty/`.` segments, **rejects** any
   `..` component (and empty keys) with `ValueError`.
2. `_blob_name` always runs keys through `_safe_key`.
3. `materialize` re-applies `_safe_key`, then
   `dest.resolve().relative_to(dest_dir.resolve())` before mkdir/download.

Hostile examples (`../escape.png`, `a/../../b.png`, `sub/../x.png`, `..`)
→ rejected by `_safe_key`. Import skips failures via existing
`ImportDirectory` exception handling.

**Local:** unchanged `resolve()` + `relative_to(root)` confinement.

**HTTP `/media`:** rejects `".." in path segments` → 400 `invalid asset path`
before streaming. Thumbnails still sanitize + `relative_to(frame_root)`.

## Residual risk (accepted for v0)

1. **Unauthenticated public Run** — search / import / media open by design;
   harden invokers before multi-user use. Non-empty `POST /api/import?path=`
   still walks container FS as the service user.
2. **`/media` order** — `storage.exists` runs before the `..` segment check;
   GCS `_safe_key` may raise `ValueError` (500) if a traversal-style id were
   already in metadata. Escape is still blocked; prefer reject/`ValueError`→400
   before exists (non-blocking polish).
3. **Bucket `force_destroy = true`** — demo operational risk.
4. **Secret / dependency scanners unconfigured** — SKIP per `rules/security.md`.
5. **UI `innerHTML` of asset ids/tags** — self-XSS residual if hostile names
   enter the corpus.

## Blocking issues

None within the 002 threat model (public v0, single-operator GCP demo).
