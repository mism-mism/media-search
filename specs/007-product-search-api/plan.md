# Plan: Product search API

## Approach

1. **Domain / store** — Add optional `product_id` to `MediaAsset`, sqlite
   `ALTER` migration, upsert/read paths, API detail/search DTOs.
2. **Text search merge** — Keep semantic KNN; add case-insensitive substring
   match on `display_name` and each tag; union by `asset_id`, keep max score;
   text-only hits use a fixed floor score below typical semantic hits so
   semantic rank stays primary when both match.
3. **Image search** — New use-case path (or shared core) calling
   `embed_image` → existing `VectorSearchPort.search`; optional `product_id`
   exact filter after collapse.
4. **API** — `POST /api/search` (JSON); `POST /api/search/by-image`
   (multipart `file` + form filters); extend `GET /api/search` with
   `product_id`; hit payload includes `product_id` + `match_kinds`
   (`semantic` | `text` | `visual`).
5. **Docs** — FastAPI schema descriptions + short note in `docs/PRODUCT.md`
   (hybrid SKU; visual similar ≠ SKU).

## Merge / rank (text)

```text
semantic_hits = KNN(embed_text(q), …)
text_hits     = assets where q ⊆ display_name OR q ⊆ any tag  (ci)
merged        = by asset_id: max(semantic_score, text_floor)
              + match_kinds union
then filters (media_type, tags AND, product_id exact) → sort score desc → top_k
```

`text_floor` = `0.15` (constant; below typical OpenCLIP positives).

## SKU hybrid (D6)

| Path | Label | Behavior |
|------|-------|----------|
| Image KNN only | visual similar | OpenCLIP cosine; no SKU claim |
| `product_id` filter | SKU-grade | exact string match on asset.product_id |
| Asset has product_id, no filter | (metadata only) | returned in hit; not auto-SKU |

## Tests

- Text merge: semantic + display_name/tag substring
- Image by-image multipart → ranked hit
- `product_id` filter exact / excludes others
- Empty image / empty text → 400
