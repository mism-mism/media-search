# media-search

ローカル優先の **メディア資産セマンティック検索**。画像・動画を取り込み、意味で探し、プレビューする。

```text
Import → OpenCLIP embed → sqlite-vec → Search UI/API
                │
        Local (001)  /  GCP Cloud Run + GCS (002)  /  IAP (003)
```

## Menu

| 行きたいこと | ドキュメント |
|--------------|--------------|
| プロダクト意図 | [`docs/PRODUCT.md`](docs/PRODUCT.md) |
| ドメイン用語 | [`docs/DOMAIN.md`](docs/DOMAIN.md) · [`docs/GLOSSARY.md`](docs/GLOSSARY.md) |
| アーキテクチャ | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| **ローカル起動** | 下の Quick start · [`docs/run-docker.md`](docs/run-docker.md) |
| **GCP デプロイ (002)** | [`docs/run-gcp.md`](docs/run-gcp.md) |
| **IAP 鍵かけ (003)** | [`docs/run-gcp-iap.md`](docs/run-gcp-iap.md) |
| Feature 仕様 | [`specs/`](specs/) |
| Agent 契約 | [`AGENTS.md`](AGENTS.md) · [`CONSTITUTION.md`](CONSTITUTION.md) |
| 検証 / CI | [`docs/CI.md`](docs/CI.md) · `./scripts/verify` |

## Features

| ID | Status | 内容 |
|----|--------|------|
| [001](specs/001-media-asset-search-vertical-slice/spec.md) | completed | Local-first 垂直スライス |
| [002](specs/002-gcp-deployment/spec.md) | completed | Cloud Run + GCS + OpenCLIP |
| [003](specs/003-iap-access/spec.md) | completed | IAP（External + Gmail allowlist） |
| [004](https://github.com/mism-mism/media-search/pull/7) | draft | Vertex eval（並行） |

## Quick start (local)

```bash
./scripts/bootstrap
# fake embedder smoke
EMBEDDER=fake uvicorn media_search.main:app --reload --port 8000
# real OpenCLIP (needs [semantic] extras)
pip install -e ".[semantic]"
EMBEDDER=local uvicorn media_search.main:app --port 8000
```

Open http://127.0.0.1:8000 — import a folder, then search with `q`.

## GCP (summary)

1. Terraform: [`infra/terraform`](infra/terraform) — see [`docs/run-gcp.md`](docs/run-gcp.md)
2. Image: `INSTALL_SEMANTIC=1` `INSTALL_GCP=1` `PREWARM_OPENCLIP=1`（CPU torch）
3. Production: `allow_unauthenticated=false` + IAP — [`docs/run-gcp-iap.md`](docs/run-gcp-iap.md)

本番の公開 URL は IAP 必須。`allUsers` 公開は実験専用。

## Project OS (template layer)

このリポジトリは Spec / Hooks / Verify / Review の Project OS も同梱します。  
ループと役割: [`docs/LOOPS.md`](docs/LOOPS.md) · [`docs/RUNTIME.md`](docs/RUNTIME.md)
