---
reviewer_role: product-reviewer
reviewer_id: keyword_product_review
---

# Product review: Reliable keyword search

Verdict: PASS

Independent Outer product evaluation of the bounded behavior in feature 015.
No blocking product gap found in AC1–AC3. This verdict does not declare overall
convergence or that the still-pending AC4 lifecycle gates have passed.

## Acceptance evidence

- **AC1:** Inspected the real SQLite query and the shared memory/SQLite cases in
  `tests/test_keyword_search.py`. SQL now searches each decoded JSON tag value;
  unchanged `json.dumps(asset.tags)` storage exercises existing escaped rows.
  Cases address Japanese substrings, quotes, backslashes, literal `%` and `_`
  with negative controls, ASCII case, whitespace-only queries, and false matches
  across tag boundaries or against serialized JSON. This repairs the reported
  keyword omission without requiring reimport.
- **AC2:** `_finalize` sorts text matches before semantic-only matches before
  applying the result limit, then uses descending existing score and asset ID.
  Tests cover both name and tag matches at `top_k=1`, with and without an indexed
  frame, ahead of a stronger semantic-only match. The wider result assertion
  preserves that semantic candidate; indexed cases retain combined match kinds
  and frame information with a single result per asset. Equal keyword scores
  are ordered by asset ID. The same explicit tie rule also applies to the
  semantic-only group by inspection.
- **AC3:** GET and POST cases use actual SQLite as well as memory repositories
  and assert Japanese tag ranking together with type, tag and exact product
  filters. Existing tests retain image search, AND-tag matching, video maximum
  frame selection and best-frame thumbnail behavior. The implementation leaves
  those paths intact. `docs/PRODUCT.md` accurately explains the new ordering,
  literal tag matching and the fact that returned score is not global rank
  across the two text-search groups.
- **AC4:** Independent `test.md` and `code-quality.md` both report PASS. The test
  reviewer independently observed **60 passed** across keyword, search-use-case,
  API, product-search and performance-009 suites; the quality reviewer observed
  **42 passed** for the new suite. I inspected these artifacts and relevant test
  assertions rather than repeating their test executions. Initial lifecycle
  runs are reported as failing solely for missing independent artifacts, with
  **94 passed, 1 skipped** in the full suite. The main agent must rerun the
  required lifecycle/feature gates after this artifact exists and record their
  actual outcomes before claiming AC4 or completion.

## Scope and limits

The correction addresses known-name/tag searches and metadata-hit visibility,
which directly supports the operator's request for stronger keyword search.
It preserves the combined search candidate strategy, response schema, score
meaning and adapter-owned SQL selection; the application does not load all
metadata. No new modes, query syntax, synonyms, automatic tagging, model changes,
UI redesign or deployment were introduced.

Deterministic fake-vector evidence establishes keyword matching and ordering,
not general semantic-model quality, production-corpus relevance or latency.
Those broader claims are outside this feature's acceptance scope. There are no
required product-behavior follow-ups; AC4 gate completion remains outstanding
work for the main agent.
