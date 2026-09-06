# 画像の日本語タグ・説明

画像の取り込み時に Gemini でタグと短い説明を生成します。画像カードの
「AIタグ・説明」を開くと内容を確認できます。ファイル名にない日本語でも
検索でき、手入力のタグ・説明・商品IDは保持します。動画は対象外です。

## 設定

| 環境変数 | 値 |
|---|---|
| `IMAGE_ANNOTATION_BACKEND` | `off`（アプリの既定）または `gemini` |
| `GOOGLE_CLOUD_PROJECT` | Gemini を利用する課金有効なプロジェクト |
| `IMAGE_ANNOTATION_MODEL` | 既定 `gemini-3.1-flash-lite` |
| `IMAGE_ANNOTATION_LOCATION` | 既定 `global` |
| `IMAGE_ANNOTATION_MAX_PER_IMPORT` | 正の整数、既定 `50` |

`pip install -e '.[gcp]'` と Application Default Credentials が必要です。
Cloud Run では実行用サービスアカウントを使います。APIキーは不要です。
画像は長辺1024px以下のJPEGに変換して Google Cloud に送信します。
`global` は日本国内の処理を保証する指定ではありません。

Gemini の利用には `aiplatform.googleapis.com` の有効化と、実行アカウントへの
`aiplatform.endpoints.predict` 権限が必要です。
[Google の権限表](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/access-control)
に従い、Terraform の `image_annotation_backend = "gemini"` でAPIと最小限の
カスタムロールを構成できます。既存環境へ手動で設定する場合は以下です。

```bash
gcloud services enable aiplatform.googleapis.com --project=laperm-507708
gcloud iam roles create mediaSearchImageAnnotator --project=laperm-507708 \
  --title='Media search image annotator' --permissions=aiplatform.endpoints.predict --stage=GA
gcloud projects add-iam-policy-binding laperm-507708 \
  --member=serviceAccount:media-search-run@laperm-507708.iam.gserviceaccount.com \
  --role=projects/laperm-507708/roles/mediaSearchImageAnnotator
```

既に作成済みのロールを再作成しないでください。手動作成後にTerraformで管理する
場合は対応するリソースを import してから plan を確認します。
`make deploy` はサービス・Import Job の両方で Gemini を有効化します。
無効化する場合は `make deploy IMAGE_ANNOTATION_BACKEND=off`。
GitHub Actions の deploy-gcp にも同名の選択肢があります。どちらも上記IAM設定を
事前に済ませる必要があります。無効化後も生成済みメタデータは検索に使われます。

## 既存画像・失敗・上限

新規アップロードはその画像を対象に取り込みます。既存画像は「ライブラリ」のアップロード欄の下にある「再取り込み」を
押すと、生成情報がない画像を最大50枚ずつ処理します。成功済みでサイズに
変更がない画像は再生成しません。タグだけを追加するときはベクトルや
サムネイルを作り直しません。デプロイだけで既存画像の一括処理は実行しません。

`failed` は生成失敗、`deferred` は今回の上限到達、`pending` は未生成です。
「再取り込み」で再試行します。失敗しても画像と作成済みベクトルは検索可能です。
1回の生成は45秒の通信タイムアウト、アプリによる即時再試行はありません。
上限は画像ごとの試行数で、課金の月額上限ではありません。失敗が続く場合は
API・権限・モデル・クォータを確認してから再実行してください。

古いSQLiteには起動・再読み込み時に生成情報用の列を追加します。
手入力の列は変更しません。GCSへの保存は既存の取り込み完了処理を使います。
画像の変更検知は既存どおりファイルサイズによるため、同じサイズでの外部差し替えは
検知できません。モデルやプロンプトを変更しても既存の成功結果は保持します。

## 確認手順

1. 内容が分かる画像を、内容を示さない名前（例 `IMG_001.jpg`）でアップロード。
2. 取り込み完了後、カードの「AIタグ・説明」に日本語が表示されることを確認。
3. 表示されたタグを検索し、その画像が見つかることを確認。
4. 再取り込み後も手入力タグ・説明・商品との紐付けが残ることを確認。

生成内容はAIの観察結果です。種別の細かな分類や季節などに誤りがあり得ます。
商品IDの特定には使いません。参照画像を使ったカテゴリの有無判定は、今後追加できる
別機能で、現在の自動タグには含まれません。

実モデル3枚の結果は [評価記録](research/016-image-auto-tags-eval.md) を参照してください。
