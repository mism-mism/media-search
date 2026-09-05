# Adoption

## Why Adoption Exists

**Template development history** and **adopted project history** are separate.

Using GitHub “Use this template” copies the template’s dogfood features
(`001`–`005`, …). Adoption removes those records so the new project’s first
feature can be `001`, while keeping the Project OS contracts and design
provenance (CONSTITUTION, ADR, REFERENCES).

## Use This Template

1. On GitHub: **Use this template** → create the new repository.
2. Clone it locally.
3. Run adoption **once**:

```bash
./scripts/adopt
```

## What `./scripts/adopt` Does

1. Verifies only **known template dogfood** features exist (fixed list in
   `scripts/adopt`). Unknown `specs/NNN-*` → **FAIL** (no silent delete).
2. Removes those features and matching `harness/reviews/*` / `harness/context/*`.
3. Rewrites `docs/PRODUCT.md`, `docs/DOMAIN.md`, `docs/GLOSSARY.md` from
   `docs/_templates/`.
4. Runs `./scripts/verify`.
5. If already adopted (no dogfood features left) → **NO-OP** + message.

`adopt` is for a **fresh template clone**. Prefer FAIL over destructive guesses.

## What Gets Removed

- Known dogfood dirs under `specs/NNN-*` (see list in `scripts/adopt`)
- Matching review/context harness artifacts

## What Gets Preserved

- `CONSTITUTION.md`, `AGENTS.md`, tool shims
- `rules/`, `agents/`, `hooks/`, `scripts/`
- `docs/ARCHITECTURE.md`, `docs/CI.md`, `docs/ADOPTION.md`
- `docs/REFERENCES.md`, `docs/adr/`
- `specs/_template/`, `specs/README.md`
- `.github/`, `.editorconfig`, `.gitattributes`

## Initialize Product / Domain

After adopt:
- Template dogfood `specs/001–007` are gone. A PR that deletes them (adoption
  commit) must not fail pre-merge for “missing specs/…/spec.md”; only **live**
  features with `specs/<feat>/spec.md` are gated (`resolve-features.sh`).
- Continue with PRODUCT/DOMAIN and `./scripts/new-feature`.

1. Edit `docs/PRODUCT.md`
2. Edit `docs/DOMAIN.md` and `docs/GLOSSARY.md`
3. Configure stack enforcers in `rules/*` when ready

## GitHub Repository Settings

Complete these in the GitHub UI (not automated by this template):

- [ ] Template repository enabled (on the **template** repo, not the project)
- [ ] Default branch = `main`
- [ ] Prefer PR-based changes (Ruleset / branch protection)
- [ ] Required status check: **`verify`** workflow job
- [ ] Force push protected on default branch
- [ ] Branch deletion protected as appropriate
- [ ] If using merge queue: require `verify` there too (`merge_group` is wired)
- [ ] Prefer one merge method (recommended: **Squash**)
- [ ] Auto-delete head branches after merge

CI contract details: [`CI.md`](CI.md).

## First Feature

```bash
./scripts/new-feature <slug>
# → specs/001-<slug>/
./hooks/pre-implement/check 001-<slug>
```

## Troubleshooting

| Symptom | Action |
|---------|--------|
| `unknown numbered feature(s)` | Inspect `specs/`; do not force-delete; update template list only for template dogfood |
| `Already adopted` | Safe; continue with PRODUCT/DOMAIN and `new-feature` |
| `verify` fails after adopt | Fix layout/shims before implementing product code |
| Want template history in the project | Don’t — keep provenance via ADR/REFERENCES instead |
