# Product

## What this is

**agentic-engineering-template** is a portable **Project OS** for AI-assisted
software engineering. It standardizes Spec-Driven Development, Harness
Engineering, Agent Review, Mechanical Verification, and Human Review.

This repository contains **no product application**. Adopting projects copy or
template from it, then fill domain and stack-specific enforcers.

## Why it exists

AI coding agents are fast and unreliable as sole judges of correctness.
Teams need:

1. Specs as source of truth
2. A harness that records evidence and context safely
3. Deterministic verification as the completion interface
4. Independent review separated from implementation
5. Human ownership of what/why/constraints/acceptance

## Non-goals

- Shipping a sample business app
- Locking adopters to one language, cloud, or AI vendor
- Fully automating multi-agent orchestration in v0
- Replacing an individual's personal Agent OS

## Adoption sketch

1. GitHub **Use this template** → clone.
2. Run `./scripts/adopt` (strips template dogfood; see [`ADOPTION.md`](ADOPTION.md)).
3. Fill `PRODUCT` / `DOMAIN` / `GLOSSARY`; configure GitHub required `verify` check.
4. Configure architecture/code-quality enforcers when the stack is known.
5. `./scripts/new-feature <slug>` starting at `001`.

## Success (v0)

A new project can run Spec → Plan → Implement → Verify → Review on day one
without inventing process. See repository README for executable acceptance
criteria.
