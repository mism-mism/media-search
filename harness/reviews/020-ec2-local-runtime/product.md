---
reviewer_role: product-reviewer
reviewer_id: independent-product-review-020
---

# Product review

PASS

Independent Outer evaluation of `feature/ec2-local` at `b954f37` against the
active 020 spec (Problem, Goal, AC1–AC4, Out of Scope, Constraints), `clarify.md`
D1–D3, `tasks.md`, `docs/PRODUCT.md`, the diff from `13335f5`, and the recorded
`verification.md`, `test.md` (PASS) and `code-quality.md` (PASS). Background
taken from the user's decisions: move from GCP to the shared EC2 box
(mk2-harness ADR 0007 §3, 2026-11-01), Gemini through an API key with tags kept,
the CLI calling the resident API after the EC2 memory measurements, and
(2026-11-03) GCS data is not copied to EC2: EC2 starts empty and GCS is not
deleted. No implementation edits or cloud/EC2 actions were made by this reviewer.

| Criterion | Evidence and assessment |
|-----------|-------------------------|
| AC1 | `_gemini_settings` in `main.py` chooses AI Studio when `GEMINI_API_KEY` is set and is shared by the annotator and the category classifier. The adapter builds `generativelanguage.googleapis.com/v1beta/models/<model>:generateContent` and puts the key only in `x-goog-api-key`. The Vertex + ADC path keeps its validation when no key is set. The model default (`gemini-3.1-flash-lite`) matches the Makefile and the GCP deploy workflow, and the request/response code is shared, so the "keep tags" decision (D2) holds structurally. The test review's mutations show the key in URL / wrong header / classifier bypass are all caught. |
| AC2 | `cli search` calls `GET /api/search` on `MEDIA_SEARCH_API` and loads no model, in line with the 2026-11-03 decision recorded in `tasks.md` (one model peaks above 2.5 GB; two froze the box). JSON shape, 512 px JPEG thumbnails, one self-contained escaped page with no scripts, and the plain one-line-per-hit output are tested end to end through the real app. This is what the Slack dispatcher needs to show results to a non-engineer without reading the media folder. |
| AC3 | `cli import` posts `/api/import`, waits on the job, prints the three lists, exits 75 with `{error: "import_busy"}` on 409 and 1 with a short code otherwise, without tracebacks or provider text. Tested, including a failed job. |
| AC4 | `docs/run-ec2.md` lists the local env, leaving out GCS/Cloud Run/project variables, `GEMINI_API_KEY` in `media.env`, the `gemini-key` extra and its failure mode, `MEDIA_SEARCH_API`, both CLI calls and the exit codes. `verification.md` records 186 passed / 2 skipped in the CI-equivalent env (the test review re-ran at `5ce3ac6`: 190 passed, 1 skipped), and an EC2 smoke run through `studio-dispatch media-search search` (exit OK, `{hits: []}` on empty data, 19 s cold) plus a memory check with one resident model and an in-process 38-photo import. |

## Against the user's intent

- **Search from Slack by a non-engineer**: the app side is delivered. The CLI
  hands the dispatcher everything (metadata, thumbnails, one page), and the
  EC2 smoke run proves the dispatcher → CLI → resident service path. It does
  not yet prove that a real image is found from Slack, because EC2 starts empty
  by the user's decision. That end-to-end check (place images in
  `/srv/media/incoming`, run `import`, search and see a hit in Slack) is owned
  by mk2-harness and the first real import; it is not claimed here.
- **Leaving GCP**: annotation and classification no longer need a GCP project
  or ADC; storage, lock, frames and DB run locally; no GCS variable is needed.
  Nothing in the diff calls GCP on the EC2 path.
- **Being able to go back**: no GCS, Cloud Run, IAP or Terraform code was
  removed (Out of Scope respected; the diff touches only the Gemini adapter,
  `main.py` settings, a new CLI, an extra, docs and tests). The Vertex path is
  unchanged and its tests pass, so a redeploy of Cloud Run still works.

## Scope

No silent scope expansion. `_gemini_settings` also removes the old
`os.environ["GOOGLE_CLOUD_PROJECT"]` KeyError in `build_runtime`, which is
needed for AC1. `requests` is only in an optional extra, as the Constraints
allow. systemd units, users, proxies and data handling stay in mk2-harness.
The per-hit thumbnail guard added in `5ce3ac6` was written into AC2 afterwards
by the implementer (`b954f37`) rather than decided by the user; it only makes a
search degrade instead of failing, so it is acceptable, but it is an
implementer-made AC change and should be named as such in the PR.

## Findings (non-blocking, should be fixed before or with the PR)

1. **D3 no longer matches the user's 2026-11-03 decision.** D3 makes rollback
   depend on comparing count, bytes, DB sha256 and top-1 of ten probe queries
   between GCS and EC2. With no data copied, that comparison cannot be run, and
   `docs/run-ec2.md` "Rollback" points to D3. The 2026-11-03 decision ("EC2
   starts empty; GCS is kept, not deleted") is recorded only as a parenthesis in
   `verification.md`. Add it to `clarify.md` (D4, decided by the user) and
   restate D3: rollback means redeploying Cloud Run against the untouched GCS
   data; GCS is not deleted (the user did not limit this to two weeks, while the
   spec's Out of Scope and the doc still say "two weeks").
2. **Rollback loses what was imported on EC2.** After the move, new images and
   tags live only in `/srv/media`. Going back to GCP returns to the old GCS
   state. The user should know this; one line in the "Rollback" section is
   enough.
3. **`plan.md` is an empty template and says "Contracts: Not applicable"**,
   although the template requires a contract section when a CLI contract is
   added. The contract is fully stated in AC2/AC3, so nothing is missing for the
   product, but the plan should point to it instead of saying "Not applicable".
4. **`docs/PRODUCT.md` still names GCP as production** (deployment posture) and
   has no 020 roadmap row. The product's deployment target has changed by the
   user's decision; update it when 020 is closed so the next spec does not
   start from the old posture.

This PASS is the product evaluator verdict only. T050 (lifecycle gates, CI on
the pushed commit, PR) remains the implementer's responsibility and is not
claimed complete here. Live outcomes beyond the recorded EC2 smoke run (a real
hit from Slack, Gemini tags from the API key on EC2, rollback rehearsal) were
not observed by this reviewer.
