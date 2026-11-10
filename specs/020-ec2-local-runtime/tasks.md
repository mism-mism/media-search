# Tasks: ec2-local-runtime

- [x] T010 Spec, AC and lean profile before pre-implement.
- [x] T020 API-key Gemini transport shared by annotator and classifier (AC1).
- [x] T030 CLI search/import with JSON and self-contained HTML (AC2, AC3).
- [x] T040 docs/run-ec2.md (AC4).
- [x] T050 Tests, verify, independent review, gates.
- [x] T060 CLI errors and filters for agent callers (AC5).

Decision during T030 (2026-11-03): the CLI talks to the resident API instead of loading its own model. Measured on EC2: one model load peaks above 2.5 GB, and two models froze an 8 GB box.
