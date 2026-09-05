# Plan: 003-iap-access

## Approach

Update Terraform for Cloud Run IAP (External brand is console/one-time setup
documented; Terraform owns IAM + invoker bindings). Remove `allUsers` when
`allow_unauthenticated=false`. Bind `roles/iap.httpsResourceAccessor` (and
Cloud Run invoker as required by current Google IAP+Cloud Run pattern) to
`var.iap_members` emails.

Keep application code unchanged (edge-only).

## Variables (intended)

| Name | Purpose |
|------|---------|
| `allow_unauthenticated` | `true` = v0 public (dev); `false` = IAP/prod |
| `iap_members` | list of `user:email@…` |
| `enable_iap` | turn on IAP service / bindings when not public |

## Docs

- `docs/run-gcp-iap.md`: OAuth External brand steps, add test users, grant
  emails, browser smoke, 403 checklist.
- Note: External brand in “Testing” mode limits test users — fine for v0 prod
  for a small allowlist.

## CD

- `deploy-gcp.yml`: when deploying prod-shaped config, do **not** pass
  `--allow-unauthenticated`; document required secret/vars for project.

## Verify

- Local FEATURE verify + reviews.
- Manual: allowlisted user opens Cloud Run URL → Google login → app UI.
- Manual negative: incognito / other account → denied.
