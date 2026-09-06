# 019 実画像・ブラウザ確認（2026-09-07 JST）

既存の猫・犬・花の写真を用い、Google Cloud `gemini-3.1-flash-lite` に3回だけ
実リクエストを送った。見本は猫1枚、カテゴリ名は「猫が写っている」。
猫は該当、犬・花は非該当となった。結果をSQLiteへ保存して再接続した後、
中立な名前IMG_0.jpg〜IMG_2.jpgからカテゴリ名検索すると猫だけがヒットした。
[実出力JSON](../../harness/eval/019-reference-categories/sample.json) を保存した。

これは複数画像入力・結果検証・保存検索経路の小さな確認である。正例には
見本と同じ写真を使っており、未知の正例への汎化、紛らわしい商品や遮蔽、
判定保留の実精度は検証していない。業務カテゴリの精度保証には使わない。
ローカルgcloudユーザー認証をメモリ内で利用し、秘密情報を保存・表示していない。
Cloud Runの本番取り込みは起動していない。adapterの直接評価なのでsource hash
は空であり、取り込みuse caseによるhash付与は別の自動テストで検証した。

ブラウザは実際のローカルFastAPI/SQLite（Gemini無効）へ接続し、1280px/390px
のChromeで登録→プレビュー→削除、ライブラリの再取り込みボタンへの誘導、
HTMLに見えるカテゴリ名/判定基準のエスケープを確認。ページエラー0、横はみ出し0。
スクリプト `/private/tmp/media-search-019-browser.cjs`、スクリーンショット
`/private/tmp/media-search-019-1280.png` と `...-390.png`。
ログイン済みIAPでの本番画面操作は未実施。このPRは未デプロイ。

最終レビューで見つかった検索キャッシュの不整合は、リポジトリ内の
`harness/eval/019-reference-categories/browser.cjs` で再現した。修正前はカテゴリ
登録後も古いカードが1枚残り失敗。修正後は登録/削除×表示済み/遅延応答の
4ケースすべて成功。カテゴリ操作は実際のローカルAPI、検索応答だけを制御して
競合を再現しており、追加のAI呼び出しはない。

再実行にはテスト用ローカルアプリを起動し、Playwrightを利用可能にして
`node harness/eval/019-reference-categories/browser.cjs` を実行する。
`CATEGORY_TEST_URL` の既定は `http://127.0.0.1:8019`、任意で `CHROME_PATH`
を指定できる。**対象のカテゴリを作成・削除するため、本番URLを指定しない。**
