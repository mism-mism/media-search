---
reviewer_role: product-reviewer
reviewer_id: independent-product-review-018
---

# Product review

PASS

Independent Outer evaluation of the implementation against the active 018 spec,
clarify decisions, plan and tasks, using the diff from `402c134` and the recorded
verification and independent Inner reviews. No implementation edits or cloud
mutations were performed by this reviewer.

| Criterion | Evidence and assessment |
|-----------|-------------------------|
| AC1 | The Makefile and GitHub deployment workflow each explicitly set `--min=0`, `--min-instances=0`, and `--cpu-throttling`. Both deployment entry points therefore express the requested zero-minimum, request-based billing policy and replace the previous warm-instance flags. The independent test review also observed the rendered Make command. |
| AC2 | Terraform adds service `min_instance_count = 0`, changes revision minimum from one to zero, and enables `cpu_idle`. The diff leaves CPU/memory, startup probe, maximum instances, IAM/IAP, environment settings, and the separate import Job unchanged. Provider-backed Terraform validation is recorded as PASS. |
| AC3 | `docs/run-gcp.md` explains automatic startup at the existing URL, container/OpenCLIP/index cold-start latency, Cloud Run-controlled idle shutdown, durable GCS state, and remaining request/startup, Job, annotation, storage and other usage costs. It promises neither immediate shutdown nor zero total billing. The separate import Job remains explicit, preserving the user's import workflow. |
| AC4 | `verification.md` records rendered local deployment and workflow shell/YAML checks, Terraform validation, and the existing regression suite with 150 passed and one optional OpenCLIP skip. Independent `test.md` and `code-quality.md` both PASS; this artifact supplies the required lean Outer product review. Final lifecycle/feature verification and PR delivery remain implementer completion steps, as detailed below. |

The implementation matches the user's recorded request to stop keeping an
always-on server. It changes only the deployment resource policy and operator
guidance; no application behavior, media/data, model, resource sizing, scheduling,
access boundary, service deletion, or billing-disable action is introduced.
`clarify.md` contains no unresolved decision, and the replaced 009 policy is
identified explicitly. No product implementation gap or unapproved scope
expansion was found.

This PASS is the product evaluator verdict, not a declaration that all delivery
steps have finished. The initial lifecycle checks failed because review artifacts
were absent. After this artifact exists, the implementer must obtain passing
feature verification and required lifecycle gates, then deliver the reviewable
PR under AC4. Those pending actions are not represented here as observed PASS.

The main agent's separately recorded production observation establishes Ready
revision/traffic, minimum and CPU-throttling configuration, and preserved IAP.
It does not measure zero idle instances, authenticated cold-start latency, or
real billing effects. Live verification is separate from this PR's acceptance
scope, so none of those runtime outcomes is asserted by this review.


## Follow-up review: maximum one

PASS

Independently reevaluated the follow-up diff from `2d8cefc` against the updated
AC1/AC2 and recorded operator decision. The original review above remains
historical evidence.

- AC1: both local and GitHub deploy commands add `--max=1 --max-instances=1`,
  while retaining both zero minimums and request-based CPU billing.
- AC2: Terraform changes revision maximum from two to one and preserves minimum
  zero, CPU idling, resource sizing, IAM/IAP and the import Job. The updated AC,
  clarification and runbook explicitly acknowledge that Google 6.x cannot
  declare the service maximum and require `gcloud run services update ...
  --max=1` after Terraform service updates. This is an explicit operational
  limitation, not a claim that Terraform preserves the unmodeled setting.
- AC3: existing cold-start, idle shutdown and remaining-charge guidance remains
  intact. The new text correctly distinguishes configured autoscaling limits
  from a hard billing cap and provides a concrete operator command.
- AC4: reviewed the recorded successful Google 6.50.0 validation and deployment
  syntax checks, plus the independent test and code-quality follow-up PASS
  artifacts. The test review records the implementer's successful regression
  and lifecycle checks. Final gates and the existing PR/CI update remain the
  implementer's pending delivery steps and are not claimed complete here.

No product gap found against the updated scope. Retaining the provider major
version follows the recorded implementation constraint; the service-maximum
operator responsibility is visible rather than silently promised away. No
application or live resource changes were made by this reviewer, and this
verdict does not establish measured runtime instance counts or billing effects.
