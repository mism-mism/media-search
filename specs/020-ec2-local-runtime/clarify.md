# Clarify: ec2-local-runtime

## Decisions

| ID | Decision | Decided by | Date |
|----|----------|------------|------|
| D1 | Move from GCP to the shared EC2 box behind Slack (mk2-harness ADR 0007 §3) | user | 2026-11-01 |
| D2 | Keep Gemini, switch Vertex + ADC to an AI Studio API key; keep existing tags | user | 2026-11-01 |
| D3 | Keep GCS data for two weeks after the move; roll back if any of count, bytes, DB sha256 or top-1 of ten probe queries differ | user (ADR 0007) | 2026-11-01 |

## Open Questions

None.
