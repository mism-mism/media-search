---
id: "018"
status: completed
profile: lean
profile_reason: "Deployment resource policy only; no domain, architecture, API, or security boundary change"
---

# Spec: Scale the search service to zero

## Goal

Honor the user's 2026-09-07 request 「常時稼働しないでほしい」 and keep
future deployments from restoring an always-on instance.

## Acceptance Criteria

- AC1. Local and GitHub deployment commands explicitly set service and revision
  minimum instances to zero, maximum instances to one, and use request-based
  CPU billing.
- AC2. Terraform declares zero service/revision minimum instances and CPU idling;
  revision maximum instances match the current production cap of one.
  Document the Google 6.x provider limitation: service maximum is set through
  CLI deployment, and must be reapplied after Terraform service changes.
  CPU/memory, IAP/IAM and import Job stay unchanged.
- AC3. Operator documentation explains idle scale-down, automatic startup on
  requests, cold-start latency, and remaining usage/storage charges without
  promising immediate scale-down or zero total billing.
- AC4. Verify rendered deployment commands, Terraform configuration validation,
  existing regression suite, lean independent reviews, and lifecycle gates.
  Deliver a reviewable PR; live service verification is handled separately.

## Constraints / Out of Scope

No service deletion, billing disablement, scheduled uptime, model change,
resource-size reduction, new background tasks, or media/data changes. This
supersedes the warm-instance deployment policy from 009 only.
