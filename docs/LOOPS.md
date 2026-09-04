# Loops

Loop Engineering binds Spec, Hooks, Verify, Review, Converge, and CI into one
**convergence control system**. v0 defines the **contract**, not an automated
loop runner (`./scripts/loop` is intentionally absent).

## Why loops exist

Failure mode addressed:

> Implement → Review → Fix are scattered, so “done” is undefined.

Closed loops define when work has **converged**.

## Surfaces

| Surface | Role |
|---------|------|
| INNER LOOP | Did this task/unit converge? |
| OUTER LOOP | Does the whole feature satisfy the Spec? |
| Converge | Outer gap → append tasks → Inner → Outer |
| CI | Enforce a claimed convergence (not revise) |
| HUMAN | Escalate / accept |

## Inner Loop

```text
Implement
  → post-implement
  → FEATURE verify
  → Self Review (optional)
  → test + code-quality evaluators
  → FAIL? Implementer fixes → repeat
  → PASS = Inner Converged
```

### Inner Converged

- `FEATURE=<id> ./scripts/verify` PASS
- Required Inner artifacts PASS: `test.md`, `code-quality.md`
- `self.md` optional (see `agents/self-reviewer.md`)

Humans are not required inside a healthy Inner Loop.

## Outer Loop

Run after tasks are Inner-converged.

### Lean Outer

- `product.md` PASS
- no unresolved gap

### Full Outer

- `product.md`, `architecture.md`, `security.md`, `final.md` PASS
- `final` also covers cross-task integration, regression, feature-wide consistency
- no unresolved gap
- (`analyze.md` remains a full-profile planning/consistency artifact as today)

### Outer Converged

Required Outer evaluators PASS **and** no open gap.

## Converge protocol

```text
Outer FAIL (gap)
  → append task(s) to tasks.md (append-only)
  → Inner Loop for new tasks
  → Outer evaluation again
```

Do **not** rewrite prior tasks to erase the gap. History of why work expanded
must remain visible.

## Evaluator classification

| Kind | Roles (existing agents) |
|------|-------------------------|
| Inner | self-reviewer (optional), test-reviewer, code-quality-reviewer |
| Outer | product-reviewer; full adds architecture, security, final-reviewer |

Required **artifact sets are unchanged** from Constitution lean/full tables.
Loops only **classify** them.

## Mutation rules

| Role | Mutates code? |
|------|----------------|
| Implementer | Yes |
| Evaluator / Reviewer | **No** |
| CI | **No** |
| Human | Decides |

Loop shape: Implement → Evaluate → FAIL+evidence → **Implementer** fixes → Evaluate.

## Human escalation

Escalate when:

- Spec ambiguity needs a decision
- High-risk judgment
- Repeated non-convergence
- Conflicting evaluator findings
- Final acceptance

Optional per-feature limits may appear in `spec.md` front matter later; v0 has
no global max iteration enforcement.

## Relationship to hooks and CI

```text
pre-implement → Implement → Inner Loop → …
Outer Loop → CONVERGED → pre-merge → CI → Human → Merge
```

Hooks remain deterministic boundary checks. CI remains the authoritative
merge adapter (`docs/CI.md`). Loops create quality; CI enforces claims.

## What v0 does not include

- `./scripts/loop` / state machine / auto-spawn of reviewers
- Mandatory `self.md`
- New cross-task artifact file
- Which AI vendor executes a role (see [`RUNTIME.md`](RUNTIME.md))

Automate runners only after real Failure Modes appear in adopting projects
(e.g. Laperm).

## Portable runtime

The Project OS defines **which roles** run and **what they evaluate**.
It does **not** define which vendor spawns them.

- Self Review: same Implementer context OK
- Independent Inner / Outer evaluators: **separate role invocation/context** required
- Same vendor allowed; renaming the Implementer turn to self-PASS is not

Details: [`RUNTIME.md`](RUNTIME.md).
