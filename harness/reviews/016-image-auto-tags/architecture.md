---
reviewer_role: architecture-reviewer
reviewer_id: independent-annotation-architecture-review
---

Verdict: PASS

Independent Outer architecture review of the uncommitted 016 implementation
against HEAD `b69866c`, performed on 2026-09-06. Reviewed the Constitution,
architecture role/rules, product architecture, feature spec, clarification,
business model and plan. Unrelated `.playwright-mcp/` and
`014-folder-nav-deep.png` were excluded. No implementation or tests were edited.

Evidence:

- Dependency direction remains inward. `domain/media_asset.py` owns the
  generated observation/provenance value without provider, database or framework
  dependencies. `ports/annotation.py` defines a byte-input/value-output contract
  and a safe failure exception. `application/import_directory.py` consumes that
  port; `adapters/gemini_annotator.py` contains authentication, HTTP endpoint,
  image conversion, request shaping and response validation. `main.py` selects
  the optional adapter. No Google SDK or credential type crosses the new port.
- Generated observations remain separate from manual metadata and product
  identity. `ImageAnnotation` is a focused value with current bounds and
  provenance; `search_tags` supplies the combined view. The plan's Contracts
  section adequately specifies additive responses, old-row behavior and safe
  failure states. There is no speculative provider framework or new service.
- Annotation-only work explicitly carries `frames=None`. The serial write path
  in `application/import_directory.py` then updates metadata without deleting,
  replacing or re-embedding frame vectors or thumbnails. Budget reservation is
  protected before concurrent provider calls; metadata/frame persistence retains
  the existing single-writer path. Provider failure records generated state
  without changing manual fields. Existing successful results are reused, while
  changed images discard stale observations under the established size check.
- `adapters/sqlite_store.py` adds two metadata columns with compatible defaults
  and runs the shared migration helper on construction and connection replacement.
  No vector schema/model change is introduced. Existing `main.py` GCS download,
  repository connection swap and import-completion upload paths continue to own
  persistence; `worker_import.py` uses the same composition root and existing
  import lock. No parallel metadata store or live-data migration is added.
- Keyword matching in SQLite and memory expands through descriptive fields;
  provenance does not become searchable text. `application/search_media.py`
  keeps existing exact-product filtering and candidate/ranking behavior while
  accepting combined tags. Search depends on persisted metadata and never calls
  the annotation provider. API response additions and rendering point inward to
  the domain value without making that value depend on Pydantic or UI details.
- `Makefile`, `.github/workflows/deploy-gcp.yml` and `infra/terraform/main.tf`
  configure both service and Import Job. Application startup defaults to `off`;
  deployment can explicitly select Gemini. Terraform conditionally provisions
  the API and prediction-only role for the existing shared runtime account.
  `docs/image-auto-tags.md` records prerequisites, enable/disable controls,
  bounded reimport, retries and retained SQLite/GCS ownership. Category-reference
  classification and embedding/store migration remain outside this feature.

Validation and limits:

- Inspected the independent Inner test and code-quality artifacts: they record
  143 passing tests with one optional OpenCLIP skip, focused annotation coverage,
  old-database reopen/replacement diagnostics and video preservation evidence.
  This reviewer inspected code and artifacts; it did not rerun those tests.
- Architecture rules still have `NOT_CONFIGURED` mechanical enforcers. This is
  a judgment-based architecture PASS, not a claim that automated dependency
  enforcement exists.
- Production build/deployment, service-account access in the Import Job, full
  feature gates and release acceptance remain separate verification obligations.
  The recorded three-image provider sample does not prove production runtime
  behavior or general corpus quality. Existing size-based freshness and the
  existing single-writer operational boundary are retained constraints.

No blocking architectural findings or required follow-ups.
