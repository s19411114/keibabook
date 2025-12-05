# 🐎 KeibaBook スクレイパー

競馬ブックから出馬表・調教・血統・コメントデータを取得するスクレイパー

---

## ⚡ クイックスタート（必読）

**環境**: Windows + Python 3.12 + `.venv` 仮想環境

**セキュリティ**: 認証情報は `config/settings.yml` に書き込まないでください。`LOGIN_ID` / `LOGIN_PASSWORD` を環境変数で渡すことを推奨します。

⚠️ **重要**: `docs/` フォルダには参考資料（JRA・地方競馬の公式URL等）が保存されています。削除しないでください。詳細は [AGENT_RULES.md](AGENT_RULES.md) を参照。

### 🔧 初回セットアップ（1回のみ）

```powershell
cd C:\GeminiCLI\TEST\keibabook
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

### 🚀 作業開始（毎回実行）

VS Code でワークスペースを開くと `.venv` が自動で有効化されます。

手動で有効化する場合:
```powershell
cd C:\GeminiCLI\TEST\keibabook
.\.venv\Scripts\Activate.ps1
```

### 🏁 アプリ起動スクリプト

Windows PowerShell:
```powershell
.\scripts\start_streamlit_win.ps1
```

バッチファイル:
```cmd
scripts\start_streamlit_win.cmd
```

どちらも:
- `.venv` を有効化
- `streamlit run app.py` を起動
- ブラウザを自動で開く

### 🖱 Windows: デスクトップショートカット作成

簡単に起動したい場合は、バッチファイル `create_shortcut.bat` でデスクトップショートカットを自動生成できます。

```cmd
create_shortcut.bat
```

デスクトップに `KeibaBook Start` ショートカットが作成されます。タスクバーにピン留めすると1クリックで起動できます。

---

## 📁 プロジェクト構成

```
keibabook/
├── app.py                    # Streamlit GUI
├── run_scraper.py            # CLI実行スクリプト
├── src/
│   ├── scrapers/            # スクレイパー本体
│   │   ├── keibabook.py     # KeibaBookスクレイパー
│   │   ├── jra_schedule.py  # JRAスケジュール取得
│   │   └── jra_odds.py      # JRAオッズ取得
│   └── utils/               # ユーティリティ
│       ├── db_manager.py    # CSV DB管理
│       ├── login.py         # ログイン処理
│       └── recommender.py   # レコメンド機能
├── data/                    # 出力データ
│   ├── db/                  # CSV DB
│   └── json/                # AI用JSON
└── config/
    └── settings.yml         # 設定ファイル
```

---

## 🎯 主な機能

- ✅ 出馬表データ取得（レース情報・馬情報）
- ✅ 調教データ取得
- ✅ 血統データ取得
- ✅ コメントデータ取得（厩舎・前走）
- ✅ 馬柱（過去3走）取得
- ✅ JRAリアルタイムオッズ取得
- ✅ CSV DB保存（重複チェック付き）
- ✅ AI用JSON出力
- ✅ Streamlit GUI

---

## 🔍 現在の課題・TODO

会話履歴から判断すると、以下が最近の作業内容です:

### ✅ 完了

### 🔄 進行中・未解決
Schedule sources (priority):
- For JRA (中央競馬): `Netkeiba` calendar is preferred to avoid unnecessary load on KeibaBook (paid site). If Netkeiba fails, fall back to `JRA` official calendar, then `keiba.go.jp` Today.
- For NAR (地方競馬): `NAR`/Netkeiba schedule fetchers are used; if unavailable, fallback to `keiba.go.jp`.

Schedule caching policy:
- Schedules (race times/venues) are cached per session in Streamlit to avoid repeated page requests; this is safe because schedules don't change frequently.
- Real-time data (like odds) are not cached by default (to prevent stale odds). Odds retrieval is done per-request and can be implemented with a short cache TTL if necessary.

Next race auto-selection:
- Next-race auto-selection is configurable in the Streamlit UI under "Developer Settings".
- Default buffer is 1 minute, which means the UI will treat a race starting within 1 minute as the "next" race.

---

## 📝 開発メモ

### データ重要度（AI評価基準）
1. 血統
2. 調教
3. 馬柱
4. スピード指数
5. レーティング
6. ファクター（印）
7. 総合指数

### 注意事項
- KeibaBookの利用規約とrobots.txtを遵守
- レート制御を実施（推奨: 10分以上の間隔）
- 一度取得したデータはキャッシュして再利用

---

### 🐛 トラブルシューティング

### ModuleNotFoundError
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Playwrightブラウザエラー
```powershell
playwright install chromium
# または強制再インストール
playwright install --force chromium
```

### 🔎 Minimal odds monitor（簡易オッズ監視）
軽量で安全な方法で指定した会場のレースオッズを監視します。デフォルトは `浦和`（地方・南関東）で、開始 10 分前と 4 分前の 2 回のスナップショットを取得します。

- 保存先: `data/odds/<race_id>/<timestamp>.json`
- 変更差分: 前回スナップショットとの単純な単勝オッズ差分（%）を記録
- 使い方（例: 浦和の 10 分と 4 分前をモニタ）:

```bash
python scripts/cli_minimal_odds.py --tracks 浦和 --offsets 10,4
```

- ヘッドフルでブラウザを立ち上げる（UIで確認したい場合）:

```bash
python scripts/cli_minimal_odds.py --tracks 浦和 --offsets 10,4 --headful
```

- 実行前に動作確認のみ行う（スケジュールに従って何が実行されるかを表示）:

```bash
python scripts/cli_minimal_odds.py --tracks 浦和 --offsets 10,4 --dry-run
```

上記は最小限の監視フローを提供します。最初は浦和 12 レースのみを対象にしてください。中央（JRA）を監視する場合は `--tracks 東京,中山,中京` のように指定して下さい（最大で 3 会場・36 レース程度）。


### ログインエラー
- `cookies.json`が正しく保存されているか確認
- `debug_login.py`でログイン処理をテスト

---

## 📚 詳細ドキュメント（参考）

### ルートレベル
- **`WORKFLOW.md`** - 開発ワークフロー統合版（Git管理、トラブル対応）⭐
- `ARCHITECTURE.md` - システムアーキテクチャ
- `DEVELOPMENT_ROADMAP.md` - 開発ロードマップ
- `PROJECT_LOG.md` - 詳細な開発履歴

### docs/ フォルダ
- `docs/COOKIE_EXPORT_GUIDE.md` - Cookie取得手順
- `docs/LOCAL_RACING_GUIDE.md` - 地方競馬対応ガイド
- `docs/ODDS_FETCHER_GUIDE.md` - オッズ取得ガイド
- `docs/VENUE_GUIDE.md` - 会場コード一覧
