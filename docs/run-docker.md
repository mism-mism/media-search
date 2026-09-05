# Docker (Feature 001 — thin local runtime)

Models are **not** baked into the image. First `EMBEDDER=local` run downloads
OpenCLIP weights into the `media_search_models` volume.

## Fake (default, light)

```bash
mkdir -p data/incoming
docker compose up --build
curl -X POST 'http://127.0.0.1:8000/api/import?path=/data/incoming'
open http://127.0.0.1:8000/
```

## Real Local OpenCLIP（精度確認はこちら）

```bash
docker compose down
docker compose --profile local up --build media-search-local
# 初回は多言語モデル取得で時間がかかる

# 重要: Fake で入れた index は使えない。必ず再 import
curl -X POST 'http://127.0.0.1:8000/api/import?path=/data/incoming'
curl -s http://127.0.0.1:8000/health
# embedder_mode=local を確認
```

UI 上部に `mode=local` とモデル名が出ます。`mode=fake` のままでは意味検索精度は出ません。

## semantic-real gate (host)

Required for Feature 001 convergence; **not** part of default `./scripts/verify`.

```bash
python3 -m pip install -e ".[dev,semantic]"
python3 scripts/prepare-golden-fixtures   # once
./scripts/semantic-real                   # FAIL if model missing or Top-K miss
```

## Notes

- Host `./data` → `/data`
- Fake DB: `media-fake.db` / Local DB: `media-local-cos.db`
- Import path inside container is `/data/incoming`
- Full offline reproducibility is a non-goal (001)
