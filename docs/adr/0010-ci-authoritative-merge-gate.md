# ADR 0010: CI as authoritative merge gate

## Context

Lifecycle hooks defend agent execution boundaries, but merge authority was only
partially defined. `FEATURE=… ./scripts/verify` also skipped reviews for
`completed`/`draft`, allowing a PR to flip `status: completed` and evade gates.
CI existed as a thin workflow without a first-class authority model
(`pull_request` / `merge_group` / push health, permissions, concurrency).

## Decision

1. **CI is the authoritative merge-time enforcement boundary**, implemented as a
   thin GitHub Actions adapter that only runs `./hooks/pre-merge/check`.
2. Triggers: `pull_request`, `merge_group`, and `push` to `main`/`master`.
   - PR / merge_group = authoritative gate
   - push = repository health check (post-hoc; does not rewind history)
3. No `paths` filters on the required workflow; internal SKIP remains honest.
4. `permissions: contents: read`; concurrency cancels superseded PR runs.
5. CI never runs LLM reviewers or mutates the repository.
6. Adapter passes `BASE_SHA` / `HEAD_SHA`; hooks remain GitHub-agnostic.
7. **Diff-touched features are never exempted by status.** Review SKIP by
   status is removed from feature-scoped verify.
8. **Draft exception:** change set may only touch `specs/<feature>/**` and
   `harness/reviews/<feature>/**`; otherwise `draft-with-implementation`.
9. Constitution bump **0.2.0 → 0.3.0**. Document required status checks in
   `docs/CI.md`.

## Alternatives

1. Prompt-only “run pre-merge before merge”
2. Put feature loops and governance rules in Actions YAML
3. Keep status-based review SKIP in verify
4. Forbid `completed` transitions inside PRs

## Consequences

- Local `./hooks/pre-merge/check` ≈ CI when BASE/HEAD match
- Parallel active features no longer confuse merge gates; status cannot bypass
- Draft spec-only PRs remain possible
- Adopters must configure Rulesets for true merge blocking
- Push failures are diagnostic, not rollback

## Sync Impact Report

Changed principle(s):

- CI authoritative merge defense
- Diff-touched features not exempted by lifecycle status
- Draft spec-only limited gate
- push = health check (post-hoc)

Affected surfaces:

| Surface | Sync |
|---------|------|
| `CONSTITUTION.md` | 0.3.0; §§4,8 status/CI |
| `AGENTS.md` | CI link; status≠exemption note |
| `docs/ARCHITECTURE.md` | CI surface |
| `docs/CI.md` | New |
| `docs/REFERENCES.md` | CI note |
| `hooks/pre-merge/check` | draft-spec-only; invalid BASE_SHA |
| `scripts/verify` | no status review SKIP; bash -n |
| `scripts/lib/resolve-features.sh` | zero SHA; draft helper |
| `.github/workflows/verify.yml` | triggers/permissions/concurrency/adapter |
| `README.md` | CI pointer |

Synchronization completed? **yes** (this change set).

## References

- Design grilling (CI authoritative merge gate)
- `docs/CI.md`
- `specs/003-ci-authoritative-merge-gate/`
- GitHub Actions: `merge_group`, concurrency, permissions
