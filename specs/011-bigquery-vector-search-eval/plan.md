# Plan: BigQuery Vector Search eval

1. Reuse 004-style query list + optional synthetic/product corpus.
2. `scripts/bq-vector-eval`:
   - `local` — OpenCLIP + in-memory/sqlite cosine (baseline)
   - `bq-byo` — upload vectors to BQ table, `VECTOR_SEARCH` with query vector
   - `bq-embed` — attempt `AI.GENERATE_EMBEDDING` / document skip if unset
3. JSON under `harness/eval/011-bigquery-vector-search-eval/`
4. Research go/no-go vs D3 latency bar.
