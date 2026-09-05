# 他社・クラウドのメディア意味検索アプローチ比較（2026-09-05）

目的: 本リポジトリの **Local-first Media Asset Search（Feature 001）** が、業界の一般的やり方に対して妥当か／どこが意図的な差分か、を一次情報ベースで比較する。

関連正本:

- [`docs/PRODUCT.md`](../PRODUCT.md)
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md)
- [`specs/001-media-asset-search-vertical-slice/spec.md`](../../specs/001-media-asset-search-vertical-slice/spec.md)
- 処理説明 HTML: [`docs/explain/processing-overview.html`](../explain/processing-overview.html)

---

## 1. 業界で共通しやすいパイプライン

公開されている実装・製品ドキュメントから見ると、視覚素材の「意味検索」はほぼ次の骨格に収束する。

```text
ingest / upload
  → (optional) auto-tag / caption / labels
  → multimodal embedding（text ↔ image / video）
  → vector index + metadata store
  → query embed → ANN / similarity
  → filters / business rules / (optional) hybrid rank
  → UI
```

根拠例:

- Google Cloud は GCS 上の画像・動画を Object Table 経由で参照し、`multimodalembedding` で埋め込み、BigQuery `VECTOR INDEX` / `VECTOR_SEARCH` で text→media 検索するデモを公式ブログで示している。  
  出典: [A multimodal search solution using NLP, BigQuery and embeddings](https://cloud.google.com/blog/products/data-analytics/multimodel-search-using-nlp-bigquery-and-embeddings)（2024-08-26）
- AWS は Titan Multimodal Embeddings で画像をベクトル化し、OpenSearch Serverless の k-NN で類似検索、必要に応じて Rekognition でオブジェクト抽出する構成を公式ブログで示している。  
  出典: [Build a reverse image search engine with Amazon Titan Multimodal Embeddings…](https://aws.amazon.com/blogs/machine-learning/build-a-reverse-image-search-engine-with-amazon-titan-multimodal-embeddings-in-amazon-bedrock-and-aws-managed-services/)
- 一般的な CLIP + Vector DB 実装解説でも「取り込み → CLIP embed → vector DB、メタは別ストア、クエリも同モデルで embed」と整理されている。  
  出典: [Multi-Modal Search: Implementing CLIP and Vector Databases (4Geeks)](https://blog.4geeks.io/implementing-a-multi-modal-search-engine-using-clip-and-a-vector-database/)（二次解説。一次製品ではないがパターンの確認用）

**本プロジェクトとの一致:** ingest → embed → local index → semantic query + metadata filter → UI/preview。骨格は業界標準に沿う。

---

## 2. 製品カテゴリ別のやり方

### 2.1 エンタープライズ DAM（Adobe Experience Manager Assets）

| 観点 | 実態 | 出典 |
|------|------|------|
| 主戦略 | **自動 Smart Tags**（ビジネス taxonomy 向け）で検索性を上げる | [Smart Tags for AEM Assets](https://experienceleague.adobe.com/en/docs/experience-manager-cloud-service/content/assets/manage/smart-tags) |
| 画像 | 視覚側面に基づくタグ | 同上 |
| 動画 | 既定で自動タグ。オブジェクト/シーン属性とアクション系の二系統 | 同上 |
| 検索 | Smart Tags と通常メタデータの組み合わせ。フルテキスト検索。類似画像検索（Asset Link の visual search）も製品機能として存在 | Smart Tags 文書 / [Asset Search (Adobe Asset Link)](https://experienceleague.adobe.com/en/docs/experience-manager-learn/assets/integrations/adobe-asset-link/asset-search) |
| 運用 | タグの人間によるモデレーション・昇格が前提。モデルは完全ではないと明記 | Smart Tags 文書（Limitations） |

**示唆:** 大手 DAM は「純粋ベクトル検索だけ」より **タグ生成 + 既存メタ検索** が中核。意味検索はタグ／類似検索として製品機能化する。

**本プロジェクトとの差分:** 001 は **AI caption/tag 生成を意図的にやらない**。Embedding 品質と Caption 品質を同時評価しないため。これは「業界フルセット」ではなく **v0 の実験設計**として妥当。後続で Adobe 型の auto-tag を足す余地はある。

---

### 2.2 メディアクラウド（Cloudinary）

| 観点 | 実態 | 出典 |
|------|------|------|
| Visual Search | **テキストまたは参照画像**で視覚的に似た画像を返す。メタデータではなく画像内容を分析 | [Visual Search](https://cloudinary.com/documentation/visual_search) |
| 別系統 | AI Content Analysis で auto-tag / caption / object detection 等 | [Cloudinary AI Content Analysis](https://cloudinary.com/documentation/cloudinary_ai_content_analysis_addon) |
| 提供形態 | SaaS。Enterprise 向け Visual Search。インデックスはプロダクト側が管理 | Visual Search 文書 |

**示唆:** 「自然言語で画像を探す」は製品として確立。実装詳細（自前 CLIP vs 独自モデル）は公開薄く、顧客は **マネージド機能を買う**。

**本プロジェクトとの差分:** 自前 Local Slice を持つ。Cloudinary は Local-first 検証には使えない（常にクラウド依存）。体験目標（text→visual）は同型。

---

### 2.3 Google Cloud（公式リファレンスアーキ）

| 観点 | 実態 | 出典 |
|------|------|------|
| パイプライン | GCS → BigQuery Object Table → `ML.GENERATE_EMBEDDING`（`multimodalembedding@001`）→ `VECTOR INDEX` → `VECTOR_SEARCH` | [GCP Blog multimodal search](https://cloud.google.com/blog/products/data-analytics/multimodel-search-using-nlp-bigquery-and-embeddings) |
| 動画 | Multimodal Embeddings API が **video + `videoSegmentConfig`（intervalSec 等）** をサポート。既定は約 16s interval、最小 4s | [Multimodal embeddings API](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/multimodal-embeddings-api) |
| Vector 製品 | Vertex AI Vector Search / BigQuery vector などマネージド選択肢 | 同上・Vector Search 製品群 |

**示唆:** GCP 公式も「multimodal embed → vector store → text query」が本線。動画は **セグメント間隔で複数 embedding** を生成するモデル。

**本プロジェクトとの関係:**

- **体験パイプラインは GCP 公式デモと同型**（だから 002 で Vertex / BigQuery 系に載せ替えやすい）。
- **001 で Vertex Vector Search / multimodalembedding API を使う**のは、Local-first・「001 で managed vector 禁止」と衝突。公式サポート＝001 の最適解ではない。
- 動画について GCP は interval ベースの **公式セグメント embed**。本プロジェクトの「代表フレーム最大3・同一画像空間」は **簡易近似**。品質は劣りうるが、2日・Local・依存最小化には合理的。002 で Vertex multimodal video embed に差し替える余地がある（Port 経由）。

---

### 2.4 AWS（公式リファレンス）

| 観点 | 実態 | 出典 |
|------|------|------|
| 構成例 | Titan Multimodal Embeddings + OpenSearch Serverless k-NN（+ 任意で Rekognition） | [AWS ML Blog](https://aws.amazon.com/blogs/machine-learning/build-a-reverse-image-search-engine-with-amazon-titan-multimodal-embeddings-in-amazon-bedrock-and-aws-managed-services/) |
| パターン | **マネージド embed + マネージド vector**。単一「Media Search」製品ではなく組み立て | 同上 |

**示唆:** クラウド大手は「全部入り 1 製品」より **embed サービス × vector ストア** の組み合わせが標準。Ports & Adapters で Local/GCP を分ける本プロジェクトの設計は、この組み立て型と整合する。

---

### 2.5 内製・中小スケールの公開事例（参考・一次性が弱いもの含む）

クリエイティブ資産 ~10万件級の内製例では、S3 + Vertex multimodal embeddings + Pinecone + FastAPI 等の **クラウド組み立て**が報告されている（個人/企業ブログ）。  
出典: [Building Semantic Search for 100k+ Creative Assets](https://jamesoncodes.github.io/articles/semantic-search-engine.html)（一次製品ドキュメントではない）。

パターンはやはり embed → managed vector。Local-first は稀。

---

## 3. 横断比較表（他社 × 本プロジェクト）

| 軸 | 大手 DAM (Adobe) | メディア SaaS (Cloudinary) | GCP 公式デモ | AWS 公式デモ | **本プロジェクト 001** |
|----|------------------|------------------------------|--------------|--------------|------------------------|
| 主検索 | タグ／メタ + Smart Tags | Visual / NL search（マネージド） | Multimodal vector | Multimodal vector | **Semantic vector** |
| Auto-tag | 中核 | 別アドオンで豊富 | 必須ではない | Rekognition 任意 | **001 ではしない** |
| Hybrid (BM25+dense) | メタ検索が強い | 製品内黒箱 | デモは vector 主 | vector 主 | **001 では融合しない** |
| 動画 | 自動タグ・シーン/アクション | 主に画像 Visual Search 文書 | セグメント embedding | 画像中心の例が多い | **代表フレーム≤3 → Asset に collapse** |
| 実行場所 | Adobe クラウド | Cloudinary クラウド | GCP | AWS | **Local（GCP は 002）** |
| Vector store | 製品内部 | 製品内部 | BigQuery / Vertex 等 | OpenSearch 等 | **局所単一ランタイム** |
| Auth / マルチテナント | あり | あり | 前提 | 前提 | **001 なし** |

---

## 4. 「今の状態は最適か」判定

評価軸を分けないと議論が混線する。

### 4.1 Feature 001（2日・価値検証）として

| 判定 | 理由 |
|------|------|
| **パイプライン骨格は最適に近い** | 業界・GCP/AWS 公式とも同型（embed → vector → filter → UI） |
| **Local-first + Port 分離は最適に近い** | マネージド製品に最初から寄せると切り分け不能。002 で GCP 公式形へ寄せる設計と両立 |
| **AI caption を後回しは 001 として妥当** | Adobe はタグ中核だが、同時導入は評価軸を壊す。業界「フルセット」ではないが v0 実験として正しい |
| **融合ランキングなしは意図的劣位（許容）** | 製品成熟域では hybrid が多い。001 は semantic 単体の効きを測るため意図的 |
| **動画フレーム簡易化は品質トレードオフ** | GCP 公式は interval セグメント embed。001 の 3 フレームは粗い。**後続で強化前提なら OK** |
| **001 で Vertex Vector Search を使わない判断は正しい** | 公式サポートはあるが、Local-first / managed 禁止 / 切り分け目標と矛盾 |

**結論（001）:** 「業界の最終形」ではないが、**今の制約（2日・Local・意味検索の独立評価）に対する最適解に近い。** 最適でないのは「企業向け完成製品」としての比較軸で見たとき。

### 4.2 本番（002 以降）として

業界・GCP 公式に寄せるなら、次が自然な進化パス。

1. Embedding: Local CLIP 級 →（候補）Vertex `multimodalembedding`（動画は `videoSegmentConfig`）
2. Vector: Local sqlite-vec 等 →（候補）Vertex AI Vector Search / BigQuery VECTOR / 他
3. Enrichment: AI tags / captions（Adobe/Cloudinary 型）を **別 Port** で追加
4. Search UX: keyword / hybrid / image-as-query（Cloudinary 型）を段階追加
5. Auth / tenancy / 運用

**Ports を保っている限り、001 の選択は本番最適を阻害しない。** 逆に 001 で Vertex に寄せると、この段階進化がしづらくなる。

---

## 5. ギャップと推奨アクション（比較検討の結論）

| 優先 | ギャップ | 推奨 |
|------|----------|------|
| P0 | 仕様に「multimodal（text↔image 同一空間）」が明示不足 | Constraints / ARCHITECTURE に追記 |
| P0 | Index 粒度（frame vs asset）が文章化不足 | plan/spec に frame 永続・asset collapse を明記 |
| P1 | 動画品質が GCP 公式より粗い | 001 は現状維持。002 または 001b で interval/segment embed を検討 |
| P1 | Auto-tag / hybrid がない | 製品ロードマップの後続 Feature に明示（001 に混ぜない） |
| P2 | image-as-query（参照画像検索） | Cloudinary 並み UX。後続 |
| — | Vertex Vector Search | **002 候補として PRODUCT に一行メモ可。001 採用は不可** |

---

## 6. 一言サマリ

他社・クラウドの「完成形」は **マネージド multimodal embed + マネージド vector +（DAMなら）自動タグ + フィルタ/hybrid** が多い。  
本プロジェクトの現状は、その完成形の **コアである semantic multimodal retrieval を、Local で切り出して証明する**配置になっており、001 の目的に対しては過不足が少ない。  
「Vertex を今使う」は業界クラウド寄せには見えるが、**自プロジェクトの Local-first 最適性を壊す**。002 で公式 GCP 形に寄せるのが比較検討上も筋がよい。

---

## 出典一覧

1. Google Cloud Blog — multimodal BigQuery search: https://cloud.google.com/blog/products/data-analytics/multimodel-search-using-nlp-bigquery-and-embeddings  
2. Vertex Multimodal embeddings API: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/multimodal-embeddings-api  
3. AWS ML Blog — Titan + OpenSearch reverse image search: https://aws.amazon.com/blogs/machine-learning/build-a-reverse-image-search-engine-with-amazon-titan-multimodal-embeddings-in-amazon-bedrock-and-aws-managed-services/  
4. Adobe Experience League — Smart Tags: https://experienceleague.adobe.com/en/docs/experience-manager-cloud-service/content/assets/manage/smart-tags  
5. Adobe Asset Link — Asset Search / visual similar: https://experienceleague.adobe.com/en/docs/experience-manager-learn/assets/integrations/adobe-asset-link/asset-search  
6. Cloudinary Visual Search: https://cloudinary.com/documentation/visual_search  
7. Cloudinary AI Content Analysis: https://cloudinary.com/documentation/cloudinary_ai_content_analysis_addon  
8. 4Geeks — CLIP + Vector DB pattern (secondary): https://blog.4geeks.io/implementing-a-multi-modal-search-engine-using-clip-and-a-vector-database/  
9. Creative assets semantic search case (secondary): https://jamesoncodes.github.io/articles/semantic-search-engine.html  
