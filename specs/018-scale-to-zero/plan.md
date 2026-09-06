# Plan

1. Set service and revision minimum instances to zero in Makefile, GitHub CD,
   and Terraform; enable request-based CPU billing.
2. Explain cold starts, durable GCS state and remaining variable costs in the
   operator guide. Preserve resources, authentication and import Job settings.
3. Inspect dry-run commands and validate Terraform; run existing gates and
   separate test/code-quality Inner evaluators, then product Outer evaluator.
4. Commit, push and open a PR. Do not apply Terraform or mutate live resources.
