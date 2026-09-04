# Architecture

## Shape of this template

Process/harness OS (not an application architecture):

```text
CONSTITUTION.md     Why / invariant principles
        ↓
RULES (rules/)      What must hold
        ↓
HOOKS (hooks/)      When enforcement happens (deterministic)
        ↓
VERIFY              Whether deterministic requirements hold (scoped)
        ↓
INNER / OUTER LOOP  Convergence control
        ↓
AGENT ROLE          Vendor-neutral contracts (agents/*)
        ↓
RUNTIME             Capability contract (docs/RUNTIME.md)
        ↓
compatible runtimes (Codex / Claude Code / Cursor / …)
        ↓
CI (adapter)        Authoritative merge-time enforcement (not a loop)
        ↓
HUMAN               Escalation / acceptance
```

Work SoT: `specs/<NNN-name>/`. Agent entry: `AGENTS.md`.  
Loops: [`LOOPS.md`](LOOPS.md) · Runtime: [`RUNTIME.md`](RUNTIME.md) ·
CI: [`CI.md`](CI.md) · Adoption: [`ADOPTION.md`](ADOPTION.md).

**Template dogfood history is not project history.** Fresh clones run
`./scripts/adopt` once before `001` product features.

## Authority split

| Layer | Role |
|-------|------|
| Inner / Outer Loops | Quality **creation** (convergence) |
| Agent roles | Vendor-neutral evaluation / mutation contracts |
| Runtime capabilities | What a tool must be able to do (not product names) |
| Hooks | Boundary defense |
| CI | Merge-time authoritative **enforcement** |
| Rulesets | Block merge unless required check passes |
| Push to main | Health check only (post-hoc) |

## Verify scope

| Invocation | Meaning |
|------------|---------|
| `./scripts/verify` | Global/meta (includes `bash -n` on harness scripts) |
| `FEATURE=NNN-slug ./scripts/verify` | Meta + completeness; **status does not skip reviews**; `reviewer_role:` presence on evaluator artifacts |

## Hooks

`pre-implement` / `post-implement` / `pre-review` / `pre-merge`.  
`pre-merge` resolves **diff-touched** features (not all active).  
Draft + spec/reviews-only → limited gate; otherwise full feature verify.

## Design principles (adopting products)

1. SOLID / DIP  
2. Domain ↛ Infrastructure  
3. Vertical slices  
4. Rule → Enforcer (else SKIP, never fake PASS)  
5. Vendor/CI adapt **to** repo hooks (OS does not call vendor agent CLIs)  
6. Code quality = Correctness / Understandability / Changeability / Simplicity  
7. Closed loops over open-loop handoffs (`docs/LOOPS.md`)  
8. Roles independent of vendors/runtimes (`docs/RUNTIME.md`)

## Reviews (unchanged sets; Loop labels)

| Profile | Inner artifacts | Outer artifacts |
|---------|-----------------|-----------------|
| lean | test, code-quality | product |
| full | test, code-quality | + architecture, security, final (+ analyze) |

Self-review optional (same context OK). Independent evaluators require a
**separate role invocation**. Implementer mutates; evaluators evaluate only.

## Parallelism (v0)

1 task → 1 branch/worktree → 1 agent context (documented; not automated).
