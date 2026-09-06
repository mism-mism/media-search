---
reviewer_role: test-reviewer
reviewer_id: independent-test-review-018
---

# Test review

PASS

Independent read-only evaluation of the implementation diff against base
`402c134` and AC1–AC4. No implementation changes or cloud mutations performed.

- AC1: Independently ran `make -n deploy`; the rendered service command contains
  `--min=0 --min-instances=0 --cpu-throttling`. Inspected the GitHub workflow and
  confirmed the same flags. Explicitly clearing both minimums covers deployment
  from the previous warm-instance configuration, rather than relying on defaults.
- AC2: Inspected the Terraform diff: service/revision minimums are both zero,
  `cpu_idle` is true, and existing maximum instances, CPU/memory, startup probe,
  IAM/IAP, and import Job configuration are unchanged. Provider-backed validation
  PASS is recorded in `verification.md`; this reviewer did not repeat it.
- AC3: Operator documentation covers idle shutdown controlled by Cloud Run,
  request-triggered startup, cold-start latency, durable GCS state, and remaining
  usage/storage costs. It promises neither immediate shutdown nor zero billing.
- AC4: Independently inspected `/private/tmp/media-search-018-pytest.out`:
  150 passed, 1 skipped, 2 dependency deprecation warnings. The optional real
  OpenCLIP skip is explicitly recorded. `git diff --check` also passed here.
  Existing import tests include overlap conflicts and frame persistence after
  local state loss. Deploy commands retain `IMPORT_JOB_BACKEND=cloudrun`, and
  `CloudRunImportJobs.enqueue` submits the separate Job with `client.run_job`;
  this change does not switch imports to the in-process background implementation.

No blocking test-strategy or AC coverage gap found for this configuration-only
scope. Rendering inspection, Terraform validation, and the unchanged application
regression suite are proportionate; no test merely duplicating configuration
constants is required.

This verdict is the test evaluator result, not a declaration of feature or merge
completion. The implementer must rerun feature verification and lifecycle gates
after all required independent artifacts exist, and deliver the PR as AC4 requires.
Initial gates failed for absent review artifacts and are not represented as PASS.
Live idle instance counts, authenticated cold-start latency, and real billing
effects are not demonstrated by these checks and remain outside this PR's stated
verification scope.

## Follow-up review — 2026-09-07

PASS

Reevaluated the configuration delta from `2d8cefc` against the updated AC1/AC2
and the explicit Google 6.x limitation in `clarify.md`; the earlier review above
is retained as historical evidence.

- Independently reran `make -n deploy`: the service command now includes both
  `--max=1` and `--max-instances=1`, while both zero minimums and
  `--cpu-throttling` remain present. The GitHub workflow diff contains the same
  additions without changing import Job arguments.
- Terraform changes revision maximum from two to one. It does not introduce the
  service maximum field rejected by Google 6.50.0. Minimums, CPU idling, resource
  sizes, access control, and application code are unchanged.
- `verification.md` records final provider 6.50.0 validation PASS and successful
  dry-run/GitHub shell syntax checks. The implementer also reports successful
  post-implement/pre-review checks and the unchanged 150-test regression result;
  no duplicate suite was necessary for this bounded configuration delta.
- The unsupported service maximum is an explicitly documented limitation, with
  a concrete command to reapply it after Terraform service updates. Neither the
  updated AC nor the runbook claims that Terraform preserves this unmodeled
  setting. The runbook also avoids treating autoscaling limits as a billing cap.
- Independently ran `git diff --check`: PASS. No blocking test-coverage gap found
  for the updated scope; no cloud mutation or provider-major migration performed.

This review does not establish production idle counts, concurrency behavior,
or billing outcomes. Updated Outer review, final gates, and PR/CI completion
remain the implementer's responsibility.
