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
