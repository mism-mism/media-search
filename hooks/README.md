# Hooks

Executable **deterministic** enforcement at agent lifecycle boundaries.
Vendor tools adapt **to** these scripts (Dependency Inversion).

## Required hooks (v0)

| Hook | When | Failure mode |
|------|------|--------------|
| `pre-implement/check` | Before coding | Ambiguity / unready feature |
| `post-implement/check` | After coding | Unverified “done” |
| `pre-review/check` | Before reviewer handoff | Review without verified inputs |
| `pre-merge/check` | Before merge (CI) | Gate bypass / missing governance |

```bash
./hooks/pre-implement/check 002-lifecycle-hooks
FEATURE=002-lifecycle-hooks ./hooks/post-implement/check
./hooks/pre-review/check 002-lifecycle-hooks
./hooks/pre-merge/check
```

Output matches verify: `[PASS]` / `[FAIL]` / `[SKIP] reason=...` plus exit code.

## Responsibility split

```text
CONSTITUTION  → Why / invariants
RULES         → What must hold
HOOKS         → When enforcement happens
VERIFY        → Whether deterministic requirements hold (scope)
REVIEW        → Whether judgment-based requirements hold
```

Hooks must **not** call an LLM to decide safety.

## Verify relationship

```text
post-implement / pre-review / pre-merge  →  ./scripts/verify
```

`./scripts/verify` alone = meta. Completion requires `FEATURE=… ./scripts/verify`.

## CI

`.github/workflows/verify.yml` is a **thin adapter**: checkout, set
`BASE_SHA`/`HEAD_SHA`, run `./hooks/pre-merge/check`.  
See [`docs/CI.md`](../docs/CI.md). CI does not run LLM reviewers.

## Adapting agent runtimes (docs only in v0)

| Runtime | Suggested adapter |
|---------|-------------------|
| CI | Call `pre-merge` (shipped) |
| Claude Code | Map native hooks to `./hooks/*/check` |
| Cursor | Rule/AGENTS contract to run hooks at lifecycle points |
| Git pre-commit / pre-push | Optionally call `pre-implement` / `pre-merge` subsets |
| Codex | Prompt/AGENTS: run the matching `./hooks/.../check` |

Do not duplicate policy inside vendor hook configs — only invoke repo scripts.

## Potential extension points (not implemented)

- pre-plan, post-plan, post-review, post-merge

Empty hook directories are intentionally omitted.
