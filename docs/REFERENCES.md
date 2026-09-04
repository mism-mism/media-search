# References

Lineage of designs adopted into **agentic-engineering-template**. Ideas were
compared and selectively integrated; none of these repositories were copied
wholesale.

## 1. GitHub Spec Kit

- **Repository:** https://github.com/github/spec-kit
- **Relevant files / docs:**
  - Constitution / `/speckit.constitution`
  - Specify, Clarify, Plan, Tasks, Checklist, Analyze, Implement, Converge
  - Spec templates and agentic SDD reference docs
- **Adopted ideas:**
  - Versioned constitution with sync impact thinking
  - Spec → Clarify → Plan → Tasks artifact chain
  - Checklist as requirements-quality review (not implementation done)
  - Analyze as read-only consistency pass
  - Numbered feature directories (`NNN-name`)
- **Adapted ideas:**
  - lean/full profiles instead of one heavy default path
  - Root `CONSTITUTION.md` instead of `.specify/memory/`
  - Single `plan.md` (Contracts section when boundaries change)
  - Converge as append-only *principle*, not mandatory ceremony
- **Rejected ideas:**
  - `.specify/` runtime layout and `specify` CLI dependency
  - Full research/data-model/contracts/quickstart file split by default
  - Soft-only enforcement without a unified `./scripts/verify`
- **Reason:** Keep Spec Kit’s intent/design/execution separation without cloning
  Spec Kit’s product surface.

## 2. OpenAI Cookbook (Codex / harness examples)

- **Repository:** https://github.com/openai/openai-cookbook
- **Relevant files / docs:**
  - `examples/codex/iterating-development-workflows-with-codex.md`
  - `articles/codex_exec_plans.md`
  - Root `AGENTS.md` patterns; Goals / repair-loop examples
  - Related: OpenAI “Harness engineering” essay
- **Adopted ideas:**
  - Short `AGENTS.md` as directory/TOC, not encyclopedia
  - Explicit Agent vs Harness ownership
  - Evidence-oriented completion; curated context with materiality
- **Adapted ideas:**
  - `harness/{context,reviews,logs}` without requiring full phase build packets in v0
  - Metrics/notes instead of heavy retrospective machinery in v0
- **Rejected ideas:**
  - Vendor-specific Codex-only workflows as mandatory
  - Raw transcript / prompt dump persistence
  - Extreme “zero human code” operational intensity as default
- **Reason:** Harness clarity without Cookbook ceremony overload.

## 3. Backblaze Vibe Coding Starter Kit

- **Repository:** https://github.com/backblaze-b2-samples/vibe-coding-starter-kit
- **Relevant files / docs:**
  - `AGENTS.md` + thin shims
  - Structural/architecture tests; `pnpm verify`
  - Agent-docs self-checks; docs as system of record
- **Adopted ideas:**
  - Canonical AGENTS + size-limited shims
  - Rule → Enforcer table; never lie with PASS
  - Single verify entrypoint; repo as SoR
- **Adapted ideas:**
  - Tech-agnostic stubs (`SKIP(reason=not_configured)`) instead of FastAPI/Next enforcers
  - Feature specs under `specs/` instead of product feature docs only
- **Rejected ideas:**
  - Bundled sample B2 application as template core
  - Stack-specific AST import tests inside this template
- **Reason:** Mechanical honesty without prescribing a product stack.

## 4. AGENTS-spec

- **Repository:** https://github.com/indisoluble/AGENTS-spec
- **Relevant files / docs:**
  - Root `AGENTS.md` contract
  - `CLAUDE.md` / Copilot thin bridges
- **Adopted ideas:**
  - AGENTS as canonical multi-tool contract
  - Thin compatibility bridges; no policy duplication
  - Protected-contract mindset (do not silently rewrite governance)
- **Adapted ideas:**
  - Precedence ladder aligned to Constitution → spec → AGENTS → rules
  - Portability budget enforced lightly in verify
- **Rejected ideas:**
  - Contract-only repo without harness/verify/review artifacts
- **Reason:** Portability of instructions; execution lives elsewhere in this OS.

## 5. agents-template

- **Repository:** https://github.com/pedrofuentes/agents-template
- **Relevant files / docs:**
  - Implementer stop rules; Sentinel independent reviewer
  - Worktree guidance; parallel dimension reviews; evals
- **Adopted ideas:**
  - Implementer ≠ Reviewer; independent final reviewer role
  - Clear agent boundaries; 1 task ↔ 1 worktree as future shape
- **Adapted ideas:**
  - Review *artifact existence* gate in v0 instead of full Sentinel runtime
  - Compressed reviewer set: product/test/(architecture/security/final)
- **Rejected ideas (v0):**
  - Mandatory multi-dimension Sentinel + SHA-bound verdict machinery
  - Strict TDD commit choreography as universal law
  - Embedding a full agent OS inside `AGENTS.md`
- **Reason:** Keep independence of review without v0 orchestration weight.

## 6. Loop Engineering discourse

- **Themes:** Microsoft LoopsBench / “From Harness Engineering to Loop
  Engineering” (2025–2026 industry discourse); Spec Kit **Converge** as
  append-only gap protocol
- **Adopted ideas:**
  - Inner Loop (task convergence) vs Outer Loop (feature/system convergence)
  - Closed loops define “done”; CI enforces claims but is not a revise loop
  - Implementer mutates; evaluators evaluate only
- **Adapted ideas:**
  - Contract-only in v0 (`docs/LOOPS.md`) — no `./scripts/loop` state machine
  - Existing lean/full review artifacts **classified**, not replaced
  - Outer `final` covers cross-task/regression without a new artifact file
- **Rejected ideas (v0):**
  - Automated loop runners / mandatory `self.md`
  - Treating CI as an Inner/Outer generate→revise cycle
- **Reason:** Convergence control without premature orchestration weight.
  See ADR 0013.

## 7. Portable agent runtime

- **Themes:** Lowest common denominator across coding agents = Markdown
  instructions + filesystem + shell; AGENTS.md as multi-tool contract
- **Adopted ideas:**
  - Canonical `AGENTS.md`; thin vendor-native bridges (`@AGENTS.md` where idiomatic)
  - Capability contract instead of product-name dependency
  - No in-repo vendor agent CLI wrappers in scripts/hooks/CI
- **Adapted ideas:**
  - Logical independence of evaluators (contractual; `reviewer_role:` presence only)
  - Self Review may share Implementer context
- **Rejected ideas (v0):**
  - Official `run-codex` / `review-with-claude` adapters inside the Project OS
  - Cross-vendor Generator≠Evaluator as a MUST
  - Grep-based vendor CLI bans in verify
- **Reason:** Survive churn of coding-agent products. See ADR 0014.

## Additional influences

- Team grilling outcomes for this repository (template adoption; Loop
  Engineering; portable agent runtime).
- Spec Kit / Backblaze inspired *mechanical* gates; this template’s hooks/CI
  are repo-owned scripts (Actions YAML is an adapter only). See ADR 0009–0014.
- Adopting projects should add rows here when they incorporate further sources.
