# Plan: GCP cost controls

1. Terraform: enable `billingbudgets` + `monitoring`; email notification channel;
   `google_billing_budget` filtered to this project; thresholds 0.5 / 0.9 / 1.0;
   amount USD 50.
2. tfvars.example documents `billing_account` / `monthly_budget_usd` /
   `budget_alert_email` (real values in gitignored tfvars).
3. Document alert-only semantics + cost drivers in `docs/run-gcp.md`.
4. `terraform apply` to create budget (requires billing-account IAM).
