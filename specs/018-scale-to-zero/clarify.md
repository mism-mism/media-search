# Clarify

The user explicitly requested no always-on server on 2026-09-07. Zero minimum
instances and request-based billing implement this preference while preserving
the existing URL and access control. Cold starts are the unavoidable tradeoff.
Both supported deploy paths must retain the setting. No human decision remains.

## Open Questions

None.

## Follow-up: preserve the current production maximum

On 2026-09-07 the main agent observed a subsequent user Cloud Console update
to revision `media-search-00027-467`: service and revision maximums are one,
revision minimum is zero, and CPU throttling remains enabled. This is an
observed existing operator preference, not a newly elicited product requirement.
Persist maximum one at both levels so neither deployment command nor Terraform
restores the earlier maximums. No additional production mutation is requested.

The existing Google provider 6.50.0 rejects service-level `max_instance_count`.
Keep Google 6.x to avoid broadening this fix into a major provider migration.
Terraform declares revision maximum one; supported CLI deployment paths explicitly
set service maximum one as well. Terraform 6.x cannot promise to preserve an
unmodeled service maximum, so the operator guide requires reapplying that cap
after a Terraform service update. This limitation is explicit in AC2.
