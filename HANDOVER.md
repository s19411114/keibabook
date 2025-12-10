Category: Handover
Status: Active

# 🎯 エージェント引き継ぎガイド

## 🚨 最初に読むべきファイル

> **重要**: 作業開始前に必ず [`AGENT_RULES.md`](AGENT_RULES.md) を確認してください。

## 📋 プロジェクト概要

競馬予想データスクレイピング＆分析アプリケーション（KeibaBook Scraper）

---

## 🐍 開発環境

**Windows + Python 3.12 + `.venv` を使用します。**

### 作業開始

```powershell
cd C:\GeminiCLI\TEST\keibabook
.\.venv\Scripts\Activate.ps1
```

### 詳細

詳細は `DEV_GUIDE.md` を参照してください。

---

## ⚠️ 重要な注意事項

### 環境について

1. **必ず `C:\GeminiCLI\TEST\keibabook` で作業**
2. **`.venv`をアクティベート** - `.\.venv\Scripts\Activate.ps1`
3. **WSL・Dockerは使用しない**

### AIエージェントへの指示

```
このプロジェクトはWindows + Python 3.12 + .venv環境を使用しています。

- 作業ディレクトリ: C:\GeminiCLI\TEST\keibabook
- Python環境: .\.venv\Scripts\Activate.ps1
- WSL・Dockerは使用しない

詳細は AGENT_RULES.md と DEV_GUIDE.md を参照。
```

---

## 📁 プロジェクト構造

```
C:\GeminiCLI\TEST\keibabook\
├── .venv\              # Python仮想環境 (Python 3.12)
├── src\                # ソースコード
│   ├── scrapers\      # スクレイパー
│   └── utils\         # ユーティリティ
├── app.py             # Streamlit UI
├── requirements.txt   # Python依存関係
└── config\            # 設定ファイル
```

---

## 🚀 よく使うコマンド

```powershell
# .venvアクティベート
.\.venv\Scripts\Activate.ps1

# スクレイピング
python run_scraper.py

# Streamlit起動
streamlit run app.py
# または
./scripts/run_nicegui.sh

# テスト実行
pytest tests\
```

---

## 📚 関連ドキュメント

- [AGENT_RULES.md](AGENT_RULES.md) - AIエージェント向けルール
- [DEV_GUIDE.md](DEV_GUIDE.md) - 開発手順書
- [README.md](README.md) - プロジェクト概要

---

## 🔄 最近の変更 (2025-11-30)

### トラックバイアス分析タブの実装
`app.py` のメンテナンス性を向上させるため、トラックバイアス分析タブ (tab3) をモジュール化しました。

- **`src/ui/track_bias_tab.py`**: tab3の全ロジック（データ取得、分析、表示）を含む新しいモジュール。
- **`app.py`**: tab3の実装を `render_track_bias_tab` 関数の呼び出しのみに簡素化。

### 次のステップ
- モジュール化されたtab3の動作確認
- 他のタブ（tab4, tab5）のモジュール化検討

---

**最終更新**: 2025-11-30

---

## ⚠️ Open Issues / Pending Work

以下は現在進行中、あるいは注意が必要な事項です。引き継ぎの際は必ず確認してください。

- **ログイン（Cookie/検証）**
	- 概要: `KeibaBookAuth` ではCookieの再利用→ページ遷移の検証（馬の数判定）を行うが、サブドメインやページレイアウトの差で未ログインと誤判定されるケースがある。
	- 影響範囲: ネットワーク実行でのフル取得（ログイン必須ページ）や自動ログイン処理。テストでは一部の実ネットワークテストはスキップされる。
	- 対策: `verify_login_by_horse_count` を改善済み（複数URL試行、ページHTMLの"ログアウト"文字列検出、context.cookies()の `tk` 存在チェック）。しかし、まだ環境差で失敗する場合あり。
	- 推奨作業: ログイン検出をさらに堅牢化（ログインユーザ名表示やプロファイルリンク検出など）、CIとローカルの再現手順を明記しておく。

- **特集ページ（`jra_special_parser`）の責務分離**
	- 概要: 特集ページの `parse_special_feature` は、もともと傾向/血統/本命等を抽出していたが、方針変更により**ドメイン固有データソース（血統/コース/AI）での抽出に統一**した。
	- 対策済み: 特集ページからの `picks` / `trends` / `pedigree_trends` 抽出は削除。現在はタイトル・自由テキストラベル(`labels`)のみを抽出。
	- 影響範囲: `exporter` は `picks` が入っている場合に出力するが、特集パーサ側からは `picks` を出さない想定。`recommender`/AI 側で判断する。
	- 推奨作業: `exporter` の仕様を明文化（特集→AI/コース/血統へ明確に振り分け）。必要に応じて `feature_data` スキーマを API ドキュメントに記載。

- **馬柱 / 過去走データの削除**
	- 概要: 運用ポリシーにより、馬柱（past_results）とギリギリ情報は収集対象から削除しました（コードでも空配列を代入している）。
	- 影響範囲: `upset_detector`, `horse_ranker` などが `past_results` を参照するが、空配列に耐性があるため既存ロジックは停止せず動作可能。
	- 推奨作業: 将来必要ならば、`past_results` の再導入を検討する際は、取得時のプライバシー/容量ポリシーを文書化し、DB スキーマ（CSV）を明確に管理する。

- **テストと Playwright 実行の警告**
	- 概要: ログに `RuntimeError: Event loop is closed` に関する `PytestUnraisableExceptionWarning` が出る場合がある。Playwright のプロセス/サブプロセスがクリーンに閉じられていない可能性。
	- 影響範囲: 直接のテスト失敗ではないが、CI の環境や他の非同期タスクで問題を引き起こす可能性あり。
	- 推奨作業: `Playwright` の `browser.close()` や `context.close()` の呼び出しを確認、pytest の終了時のループクリーンナップ（`pytest-asyncio` と `asyncio.get_event_loop().close()` の扱い）を見直す。

- **DB race_id データ型問題**
	- 概要: CSV から読み込む際に `race_id` が数値でロードされるケースがあり、比較が失敗することがあった（`is_race_fetched` の検証で発生）。
	- 対策済み: `CSVDBManager.is_race_fetched` で `df['race_id'].astype(str) == str(race_id)` に統一して比較。
	- 推奨作業: CSV 各列の型を正規化・保存用 API を追加して、読み込み時に型を保持するようにする。

- **ドキュメントの整合性**
	- 概要: README / DEV_GUIDE / exporter の docstrings は特集・馬柱収集方針に更新済みだが、すべてのドキュメント（例: ARCHITECTURE, migration docs, sample_output) を順次アップデートする必要がある。
	- 推奨作業: `DOC_MANIFEST.json` に「ドキュメント整合性チェック」を追加して、収集ポリシーに一致するかを確認するCIチェックを導入。

	---
	## 2025-12-11 追記: NiceGUIテーマ + 調教レポート
	- Branch: feat/nicegui-theme-training
	- 内容: NiceGUI のダーク/ライト切替（アプリ内テーマ、ブラウザ拡張に依存しない表示）、トレーニング（調教）レポート生成ボタンとレポート表示エンドポイント（`/training_report/<name>`）を追加しました。`src/utils/schedule_utils.py` の夜間レース時刻ロールオーバー対応と、`_get_race_number` の race_id 型耐性修正も含まれます。
	- 影響: 生成レポートは `data/reports/` に保存され、`.gitignore` に追加されました。
	- 次の推奨作業: 調教データ検出ロジック（`_parse_training_data`）の追加パターン対応、NiceGUIの配色微調整、CIにレポート生成のテスト追加。


---

この一覧は現状の主要課題です。どれを優先して引き継ぎますか？（例: ログインの更なる堅牢化、イベントループ警告対策、ドキュメント整合性チェックの実装など）