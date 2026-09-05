# Media Search Server — Bootstrap Prompt (summary)

**This file is a launch summary, not the Source of Truth.**
Authoritative decisions live in:

- [`docs/PRODUCT.md`](../PRODUCT.md)
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md)
- Active feature `specs/001-*/spec.md` (and `clarify.md`)

Do not treat this prompt as a substitute for those documents.
Before implementation, read the docs above and resolve Open Questions in clarify.

---

# Runtime / Deployment Constraint

本番環境は Google Cloud Platform（GCP）を使用します。

ただし、開発の第一段階では GCP への接続なしで
ローカル環境だけでアプリケーション全体を実行できるようにしてください。

開発順序は、

```text
Local
→ Container / reproducible runtime
→ GCP deployment
```

とします。

最初から GCP へデプロイしながら開発しないでください。

# Local-first requirement

ローカル環境では少なくとも以下が可能であることを目標にしてください。

- アプリケーション起動
- 画像・動画素材の取り込み
- Metadata 生成・保存
- 局所ベクトルストアによる意味検索（semantic search）
- 検索結果表示
- 素材詳細表示・原素材 preview
- テスト
- FEATURE verify（決定的ゲート + 必須の semantic-real gate）

GCP の認証情報が存在しなくても、
主要な Vertical Slice を確認できる構造にしてください。

# Vector search (v0 / Feature 001)

意味検索（local vector search）は Feature 001 の正式要件です。

ただし、

- managed / distributed な大規模 vector infrastructure は 001 に持ち込まない
- Local / single-runtime に閉じる既存エンジンを Adapter として使う
- ANN エンジン本体の自作はしない（作るのは Product の Vector Search capability）

詳細定数・collapse 規則・対応フォーマット等は **001 spec** を正とする。

# GCP target

最終的には GCP へ配置できる Architecture にしてください。

ただし、現時点で具体的な GCP サービスを先に決めないでください。
Feature 001 が収束するまで、002 の GCP サービス選定を開始しないでください。

Product / Domain / Use Case を設計した後、

- Application runtime
- Media storage
- Metadata persistence
- Search / index（含む vector）
- AI enrichment / embedding
- Secrets / configuration
- Observability

それぞれについて、Local implementation と GCP implementation の境界を提案してください。

GCP 固有 SDK や API を Domain / Application の中心へ漏らさないでください。

例（名前は Domain 設計後に決めてよい）:

```text
MediaStorage
    ├ LocalFilesystemMediaStorage
    └ GcpMediaStorage

VectorSearch
    ├ LocalVectorSearch
    └ GcpVectorSearch

EmbeddingPort
    ├ FakeEmbedder
    └ LocalModelEmbedder / GcpEmbedder
```

上記をそのまま実装する必要はありません。

# Feature split

```text
001 — Local-first Media Asset Search Vertical Slice
002 — GCP deployment（Local adapters → GCP adapters、可能な限り同じ Product AC）
```

# Important

「将来 GCP へ載せるから」という理由だけで、

- Microservices
- Kubernetes
- 複雑な IaC
- Pub/Sub
- 分散 Job 基盤
- 大規模 Vector infrastructure
- GCP 専用抽象化

を v0 / 001 へ追加しないでください。

まずローカルで 1 本の Vertical Slice を完成させてください。

その Vertical Slice が完成してから、
同じ Application / Domain を変更せず、
Infrastructure Adapter を差し替えて GCP へ配置できることを目指してください。

# Docs are Source of Truth

実装・レビュー・完了判定は、このプロンプトではなく
PRODUCT / ARCHITECTURE / 001 spec に従ってください。
