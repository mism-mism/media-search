# media-search

画像・動画を取り込み、キーワードや意味で探せるメディアライブラリです。
フォルダ・商品で素材を整理し、画像の内容から生成した日本語タグや説明も検索に使えます。
ローカルではSQLite、Google CloudではCloud Run + GCSを使い、本番へのアクセスはIAPで制限します。

## できること

| 機能 | 内容 | 詳細 |
|---|---|---|
| 検索 | OpenCLIPによる意味検索と、名前・タグ・説明のキーワード検索。画像による類似検索や商品・タグの絞り込みはAPIでも利用可能 | [検索仕様](specs/015-keyword-search-relevance/spec.md)・[商品検索API](specs/007-product-search-api/spec.md) |
| 素材管理 | JPG・PNG・MP4の複数アップロード、フォルダ整理、商品との紐付け、プレビュー | [ライブラリ仕様](specs/006-media-library/spec.md) |
| 日本語AIタグ・説明 | 取り込み時にGeminiで画像を説明し、手動の情報と分けて保存・検索 | [設定・使い方](docs/image-auto-tags.md) |
| 見本カテゴリ判定 | 見本画像と判定基準から「該当・非該当・判定保留」を保存。該当したカテゴリ名だけを検索用タグに追加 | [設定・使い方](docs/reference-categories.md) |
| 再取り込み | 未生成・失敗・上限で見送った画像を処理し、進捗と結果を表示 | [取り込み導線](specs/017-reimport-entry/spec.md) |
| GCP運用 | IAPによるアクセス制限、Cloud Run Jobsでの取り込み、非アクセス時のスケールゼロ、予算通知 | [GCP運用](docs/run-gcp.md) |

検索用ベクトルはOpenCLIPで生成し、SQLite / sqlite-vecに保存します。
Geminiは取り込み時の画像解析に使い、検索時には呼び出しません。
手動タグ・AIタグ・見本カテゴリの判定は区別して保持し、画像から商品コード（SKU）を推測して設定することはありません。

### 本番反映状況（2026-09-07時点）

- 検索改善、日本語AIタグ・説明、再取り込みボタン、常時稼働の解除は本番反映済みです。
- 見本カテゴリ判定は[PR #22](https://github.com/mism-mism/media-search/pull/22)で実装・検証済みですが、本番にはまだ反映していません。
- 見本カテゴリの実画像確認は猫・犬・花の3枚による小規模な確認です。正例には見本と同じ写真を使っており、業務画像での精度は別途確認が必要です。[検証記録](docs/research/019-reference-category-eval.md)

## 使い方

1. 「ライブラリ」でフォルダを選び、画像・動画をアップロードします。商品を紐付ける場合は、先に「商品」タブで登録します。
2. 取り込み完了後、上部の検索欄に「白いボトル」「海辺の風景」などを入力します。
3. 画像カードの「AIタグ・説明」で生成内容を確認します。生成にはGeminiの有効化が必要です。
4. 既存画像を処理する場合は、ライブラリのアップロード欄の下にある「再取り込み」を押します。対象は全フォルダです。

見本カテゴリを利用できる環境では、「見本カテゴリ」タブでカテゴリ名・判定基準・見本画像1〜3枚を登録し、
「ライブラリで再取り込みへ」から判定を実行します。最大5カテゴリを登録できます。
カテゴリの登録・削除では全画像のカテゴリ判定が未判定に戻るため、再取り込みが必要です。

## ローカル起動

Python 3.10以上と、動画処理用の`ffmpeg`を用意してください。
実際の意味検索にはOpenCLIPを使用し、初回起動時にモデルのダウンロード・読み込みが発生します。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,semantic]"
EMBEDDER=local python -m uvicorn media_search.main:app --port 8000
```

[http://127.0.0.1:8000](http://127.0.0.1:8000)を開いてアップロード・検索を試せます。
ローカルデータは既定で`data/`、取り込み元の素材は`data/incoming/`に保存します。
Dockerでの起動は[Docker起動手順](docs/run-docker.md)を参照してください。

画面やAPIの動作だけを確認する場合は、仮想環境で以下を実行できます。
`fake`は動作確認用で、意味検索の精度評価には使えません。

```bash
python -m pip install -e ".[dev]"
EMBEDDER=fake python -m uvicorn media_search.main:app --port 8000
```

### Geminiの有効化と処理上限

ローカルでは画像解析は既定で無効です。有効化には`.[gcp]`の追加依存、Google Cloudの認証・API・権限設定が必要です。
[日本語AIタグの設定](docs/image-auto-tags.md)に沿って設定してください。

| 環境変数 | 既定・用途 |
|---|---|
| `IMAGE_ANNOTATION_BACKEND` | アプリの既定は`off`。`gemini`で画像解析を有効化 |
| `GOOGLE_CLOUD_PROJECT` | Geminiを呼び出すプロジェクト |
| `IMAGE_ANNOTATION_MAX_PER_IMPORT` | 一般のAIタグ・説明生成は1回の取り込みで最大50画像 |
| `CATEGORY_MAX_PER_IMPORT` | 見本カテゴリ判定は1回の取り込みで最大50画像。一般のAIタグ生成とは別の上限 |

成功した結果は再利用し、失敗・上限到達で未処理の画像は再取り込みで再試行します。
見本カテゴリ判定では、見本だけでなく対象画像の内容の変更も確認します。
GCPではWebサービスとImport Jobの両方に同じ設定を渡してください。

## GCP運用と費用

本番はCloud Run（東京）+ GCS + IAPの構成です。
素材とSQLiteのスナップショットをGCSに保持し、取り込みはCloud Run Jobsで実行します。

- Webサービスは**最小0台・リクエスト時課金**です。非アクセス時は0台まで縮小し、次のアクセス時に起動待ちが発生します。
- `make deploy`とGitHub Actionsはサービス・リビジョンの最大台数を1に設定します。Terraformのサービス上限に関する制約は[GCP運用手順](docs/run-gcp.md)を参照してください。
- Webサービスを常時起動しなくても、起動・リクエスト処理、取り込みジョブ、Gemini、GCS保存・転送などの従量料金は発生します。
- 月50 USDの予算は**通知用**です。超過しても自動停止せず、課金の上限にはなりません。

デプロイ前に[インフラ構成](infra/terraform)と[GCP運用手順](docs/run-gcp.md)、[IAP設定](docs/run-gcp-iap.md)を確認してください。
既存環境へのデプロイは次のコマンドです。WebサービスとImport Jobの両方を更新し、既定でGeminiを有効化します。

```bash
make deploy IMAGE_TAG=019-reference-categories
```

## 検証と次の確認

```bash
make test
./scripts/verify
FEATURE=019-reference-categories ./scripts/verify
```

自動テストはプロバイダーを模した応答で動作・境界条件を確認します。
実モデルの検索精度確認については[意味検索の検証手順](docs/run-docker.md)を参照してください。
次の確認事項は、見本カテゴリ判定の本番反映、業務画像での検索・分類精度、停止状態からの起動待ち時間と実際の利用料金です。

## ドキュメント

| 内容 | リンク |
|---|---|
| プロダクトの目的 | [PRODUCT](docs/PRODUCT.md) |
| ドメイン・用語 | [DOMAIN](docs/DOMAIN.md)・[GLOSSARY](docs/GLOSSARY.md) |
| アーキテクチャ | [ARCHITECTURE](docs/ARCHITECTURE.md) |
| 機能仕様・評価実験 | [specs](specs/) |
| エージェントの作業契約 | [AGENTS](AGENTS.md)・[CONSTITUTION](CONSTITUTION.md) |
| 検証・レビュー・CI | [LOOPS](docs/LOOPS.md)・[RUNTIME](docs/RUNTIME.md)・[CI](docs/CI.md) |

このリポジトリにはSpec / Hooks / Verify / Reviewの作業基盤も同梱しています。
`./scripts/bootstrap`はドメイン・用語ドキュメントの初期化用で、アプリの依存関係をインストールするコマンドではありません。
