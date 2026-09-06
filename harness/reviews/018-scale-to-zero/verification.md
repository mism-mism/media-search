# Verification evidence

- `make -n deploy`: rendered command contains `--min=0`, `--min-instances=0`,
  `--cpu-throttling`; no cloud command was executed.
- GitHub deploy workflow uses the same three flags. YAML parsing and `bash -n`
  pass for its three run blocks and the local rendered deploy script.
- `terraform -chdir=infra/terraform validate`: PASS, using the existing initialized
  Google provider 6.50.0 through TF_DATA_DIR (sandbox plugin launch retried outside
  sandbox). No Terraform plan/apply or live resource change was executed here.
- Existing regression suite: 150 passed, 1 skipped (optional real OpenCLIP test),
  2 existing dependency deprecation warnings. Full test output retained locally
  at `/private/tmp/media-search-018-pytest.out`.
- Initial post-implement and pre-review calls ran the regression suite successfully
  but failed review completeness because independent artifacts were not yet
  available. Gates will be rerun after evaluator outputs exist; no gate bypass.
- Production evidence separately observed by the main agent on 2026-09-07:
  revision `media-search-00026-j4g` Ready=True, 100% traffic; service/revision
  minimum annotations absent (default zero), CPU throttling true and IAP true.
  Previous revision has no traffic or tags. This confirms configuration, not
  a measurement of idle instance count or an authenticated cold-start smoke.

## Final local convergence

Independent test, code-quality and product evaluators all returned PASS. After
those artifacts existed, `post-implement`, `pre-review` and explicit
`FEATURE=018-scale-to-zero ./scripts/verify` all passed on 2026-09-07. Each
feature verify reported 14 passed, 0 failed, 10 explicitly unconfigured/skipped
harness checks; the application regression suite remained successful.

`pre-merge` also passed against implementation commit `eb72560` and the diff
from `origin/main`: 4 passed, 0 failed, 1 unchanged-constitution skip. The branch
was pushed and [PR #21](https://github.com/mism-mism/media-search/pull/21) opened.
The feature delivery ends at an open PR; no merge or Terraform apply is claimed.

## Follow-up: observed maximum-one configuration

The main agent observed a user Console update to `media-search-00027-467`,
with service/revision maximum one, revision minimum zero and CPU throttling true.
This follow-up does not mutate production. CLI deploy paths now explicitly use
`--max=1 --max-instances=1`; Terraform revision maximum is one.

Google provider 6.50.0 rejected service-level `max_instance_count` with an
unsupported-argument error. The final configuration retains Google `~> 6.40`,
does not declare that unsupported field, and documents explicitly reapplying
`gcloud run services update ... --max=1` after Terraform service changes. No
claim is made that Terraform 6.x preserves the unknown service-level maximum.

Final Google 6.50.0 `terraform validate` passed. Updated local dry-run and three
GitHub run blocks passed shell syntax checks, with both CLI maxima set to one.
Minimum zero, CPU idling, CPU/memory, IAP/IAM and the import Job remain intact.

Independent test, code-quality and product reevaluations of the maximum-one
delta all passed. Subsequent post-implement, pre-review and explicit feature
verify passed. Installed `gcloud run deploy --help` also advertises both
`--max` and `--max-instances`. No application or provider requirement change
is included in this follow-up.
