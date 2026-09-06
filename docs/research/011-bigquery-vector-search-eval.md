# 011 — BigQuery Vector Search evaluation

Date: 2026-09-06  
Clarify: D1–D7 locked (eval only; BYO + BQ-embed compared; interactive warm p95 &lt;1s; no Vertex interactive default; 004-like + product_id when available; spend ≤ few tens USD; profile full).

## Verdict

**no-go for interactive UI default cutover** (`no-go-interactive`).

Production remains OpenCLIP + sqlite-vec on Cloud Run (GCS-synced state).  
BigQuery `VECTOR_SEARCH` is a valid **batch / offline / analytics** path when BYO vectors are acceptable.

## Protocol

| Pass | What | Result |
|------|------|--------|
| `local` | OpenCLIP + in-process cosine on `data/corpus-web` (18 images, 20 JA/EN queries) | hit@1 **0.90**; mean search proxy **~0.033s** |
| `bq-byo` | Same OpenCLIP vectors → BQ table + `VECTOR_SEARCH` (COSINE, top_k=1) | hit@1 **0.90**; search **p95 ≈ 1.8–2.1s** |
| `bq-embed` | BQ/Vertex `AI.GENERATE_EMBEDDING` | **skipped** (`BQ_EMBED_ENABLE` unset) — D6 spend + D4 spirit; BYO already exercises `VECTOR_SEARCH` |
| product_id sample | D5 second corpus | **not run** — no product-tagged export wired; SKU Recall remains `scripts/sku-embedder-eval` (008) |

Artifacts: `harness/eval/011-bigquery-vector-search-eval/summary.json`

```bash
GOOGLE_CLOUD_PROJECT=laperm-507708 ./scripts/bq-vector-eval
```

## Interpretation

1. **Quality**: BYO BQ matches local hit@1 on the locked text→image set (same model vectors).
2. **Latency**: BQ query p95 (~2s) fails D3 (&lt;1s) for interactive UI default — even on a tiny table, job round-trip dominates.
3. **Embedding path**: Generating embeddings inside BQ/Vertex was not required to judge `VECTOR_SEARCH` latency; default skip keeps cost under D6 and avoids reopening 004 interactive-Vertex caution.
4. **Ops**: Durable vectors in BQ still attractive for warehouse / batch similarity; not a drop-in replacement for warm Cloud Run search.

## Go / no-go matrix

| Question | Answer |
|----------|--------|
| Cut over Library / `/api/search` to BQ now? | **No** |
| Keep evaluating BQ for batch / export / analytics? | **Yes (optional follow-on)** |
| Change production embedder? | **No** (unchanged OpenCLIP) |
| Spend this run | Small corpus inserts + VECTOR_SEARCH queries (well under tens USD) |

## Follow-ons (out of 011)

- Indexed VECTOR_SEARCH / VECTOR INDEX + warm connection pool (may still miss &lt;1s interactive bar).
- Product-tagged corpus pass when library export exists.
- Opt-in `BQ_EMBED_ENABLE=1` notebook for remote-model quality vs OpenCLIP (cost-gated).
