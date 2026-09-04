# Code Quality Rules

Code quality supports **Correctness, Understandability, Changeability, and
Simplicity**. Cleverness, abstraction density, and minimum line count are not
quality goals.

Every rule declares **Evaluation**: `Mechanical`, `Judgment`, or both.
Mechanical rules need an Enforcer command when the adopting stack configures
them. Until then verify reports `SKIP(reason=not_configured)`.

## Principles

| Rule | Evaluation | Enforcer | v0 |
|------|------------|----------|-----|
| Prefer explicit over implicit; simple over clever; cohesive over generic | Judgment | code-quality-reviewer | required |
| Prefer composition over unnecessary inheritance | Judgment | code-quality-reviewer | required |
| Prefer domain language over vague technical labels | Judgment | code-quality-reviewer | required |
| Optimize for changeability and understandability, not cleverness | Judgment | code-quality-reviewer | required |

## Responsibilities

| Rule | Evaluation | Enforcer | v0 |
|------|------------|----------|-----|
| A function/module SHOULD have one clear reason to change | Judgment | code-quality-reviewer | required |
| Avoid god objects / mixed abstraction levels / hidden side effects | Judgment | code-quality-reviewer | required |
| Avoid unnecessary indirection and speculative generalization | Judgment | code-quality-reviewer | required |

## Duplication

| Rule | Evaluation | Enforcer | v0 |
|------|------------|----------|-----|
| Do not abstract merely because two snippets look alike | Judgment | code-quality-reviewer | required |
| Abstract only when they share the same concept and change for the same reason | Judgment | code-quality-reviewer | required |

## Naming

| Rule | Evaluation | Enforcer | v0 |
|------|------------|----------|-----|
| Names MUST express domain (or harness) intent | Judgment | code-quality-reviewer | required |
| SHOULD avoid `utils` / `helpers` / `manager` / `common` / `misc` unless that responsibility is real | Judgment | code-quality-reviewer | required |

Word bans are **not** mechanical in v0 (false positives). Reviewers judge
whether a name hides a god object or a genuine concept.

## Error handling

| Rule | Evaluation | Enforcer | v0 |
|------|------------|----------|-----|
| Failure paths must be explicit | Judgment (+ Mechanical when linters exist) | NOT_CONFIGURED / reviewer | SKIP + required review |
| Errors must not be silently swallowed | Judgment (+ Mechanical when configured) | NOT_CONFIGURED / reviewer | SKIP + required review |
| Boundary failures translated at the boundary | Judgment | code-quality-reviewer | required |
| Domain must not depend on infrastructure-specific errors | Judgment | code-quality-reviewer + architecture-reviewer | required |

## Comments

| Rule | Evaluation | Enforcer | v0 |
|------|------------|----------|-----|
| Comments explain WHY, constraints, or non-obvious decisions | Judgment | code-quality-reviewer | required |
| Do not comment WHAT the code already says | Judgment | code-quality-reviewer | required |

## AI-generated code

Agents MUST NOT:

- introduce abstractions without a current requirement
- create generic frameworks for a single use case
- add fallback behavior not requested by the spec
- leave placeholder implementations
- suppress errors to make tests/verify pass
- duplicate business rules across layers

| Rule | Evaluation | Enforcer | v0 |
|------|------------|----------|-----|
| No speculative AI abstractions / placeholders / error suppression | Judgment | code-quality-reviewer | required |

## Mechanical quality (stack adapters)

| Rule | Evaluation | Enforcer | v0 |
|------|------------|----------|-----|
| Formatting | Mechanical | NOT_CONFIGURED | SKIP |
| Lint | Mechanical | NOT_CONFIGURED | SKIP |
| Type safety | Mechanical | NOT_CONFIGURED | SKIP |
| Complexity threshold | Mechanical | NOT_CONFIGURED | SKIP |
| Dead code detection | Mechanical | NOT_CONFIGURED | SKIP |

Wire real commands in adopting projects; never fake PASS.

## Boundary with Architecture Review

| Code Quality (local) | Architecture (system) |
|----------------------|-------------------------|
| readability, cohesion, naming | dependency direction, DIP |
| local accidental complexity | cross-component structure |
| local unnecessary abstraction | architectural layers/boundaries |
| error handling locality / testability | domain leakage across boundaries |

## How to configure Mechanical enforcers

1. Choose stack tools (formatter, linter, typechecker, complexity, dead-code).
2. Replace `NOT_CONFIGURED` with commands.
3. Invoke them from `./scripts/verify`.
4. Keep Judgment rules on `code-quality-reviewer`.
