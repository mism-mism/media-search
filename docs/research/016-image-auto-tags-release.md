# 016 リリース記録

2026-09-06、実装コミット `a0eb9ae59e8a5bfbb73cc43798f141a5f75614bc` を
独立fullレビュー、ローカルのライフサイクルゲート、
[PR CI](https://github.com/mism-mism/media-search/actions/runs/34038811288) の成功後に反映した。
[PR #18](https://github.com/mism-mism/media-search/pull/18) にリリース結果をまとめる。

- コンテナ: `asia-northeast1-docker.pkg.dev/laperm-507708/media-search-repo/media-search:016-a0eb9ae`
- 配布digest: `sha256:94cec8321b7a6b8991c13e49289f7d064fa6b97f1638e28c0db81e82ad0ea1f6`
- Cloud Run: `media-search-00023-k52`、Ready、トラフィック100%。Import Jobも同じ版へ更新。
- IAP enabledを確認。匿名の `/health` はHTTP 302でGoogle認証へ転送。
- 実行SAには `aiplatform.endpoints.predict` だけを含むカスタムロール
  `mediaSearchImageAnnotator` を付与。APIは既に有効だった。

## 本番実行環境の生成確認

`media-search-import-bnv2j` が 2026-09-06T14:29:19Z に正常終了した。
通常の取り込み処理の代わりに、実行時だけ引数を上書きし、32×32の白いPNGを
1枚作成して本番の `_build_annotator()` で生成した。画像コーパスの取り込み・
本番DBへの保存は行っていない。ジョブ本体の引数は検証後も
`-m media_search.worker_import` のままと確認した。

Cloud Loggingの実出力:

```json
{"check":"production_job_gemini","model":"gemini-3.1-flash-lite","status":"ready","tags":["真っ白","背景","無地","プレーン","白一色","シンプル","テクスチャなし","明るい","空白","ミニマル"]}
```

これにより、配布済みコード・ジョブ設定・実行SA・Gemini呼び出しの接続を確認した。
ローカル実画像3枚の生成とSQLite検索は[評価記録](016-image-auto-tags-eval.md)を参照。
コンテナ起動およびキャッシュ済みOpenCLIPで512次元の実埋め込み生成も成功した。

## 利用時の確認と制限

既存画像の一括バックフィルは未実施。アップロードまたは次の取り込みで、
既定50枚まで日本語タグ・説明を生成する。参照画像によるカテゴリ有無判定は未実装。
IAPログイン済みブラウザでの本番アップロード→検索の通し操作は、このリリースでは
検証していない。利用者向けの[確認手順](../image-auto-tags.md#確認手順)を参照。

デプロイログはローカルの
`/private/tmp/media-search-016-logs/logs/2026-09-06/e4bb75d4-a207-4499-bf50-7d7aed8fe9dd/`
に保持。認証情報は評価・リリース記録に含めていない。
