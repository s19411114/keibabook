Category: Overview
Status: Active

# 🐎 KeibaBook スクレイパー

競馬ブックから出馬表・調教・血統・コメントデータを取得するスクレイパー

---

## ⚡ クイックスタート（必読）

**環境（推奨）**: Zorin/Ubuntu + Python 3.12 + `.venv` 仮想環境

**セキュリティ**: 認証情報は `config/settings.yml` に書き込まないでください。`LOGIN_ID` / `LOGIN_PASSWORD` を環境変数で渡すことを推奨します。

**開発ツール（必須）**: ローカルで作業する場合、プロジェクトルートに仮想環境を作成し、開発ツールをインストールして `pre-commit` を有効にしてください。

```bash
# 1) 仮想環境を作成して有効化
python3 -m venv .venv
source .venv/bin/activate

# 2) 実行環境と開発ツールをインストール
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r dev-requirements.txt

# 3) pre-commit を有効化する（コミット前に検査が走ります）
pre-commit install
pre-commit run --all-files  # 任意: 全ファイルを検査
```

⚠️ **重要**: `docs/` フォルダには参考資料（JRA・地方競馬の公式URL等）が保存されています。削除しないでください。詳細は [AGENT_RULES.md](AGENT_RULES.md) を参照。

### 🔧 初回セットアップ（1回のみ） - Linux (Zorin/Ubuntu 推奨)

```bash
cd ~/GeminiCLI/TEST/keibabook
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium
```

Windows 用スクリプトは `scripts/windows_archived` に移動しています。

### 🚀 作業開始（毎回実行）

VS Code でワークスペースを開くと `.venv` が自動で有効化されます。
注: VS Code が自動で有効化するため、ターミナルのプロファイルやシェルの初期化ファイルで `source .venv/bin/activate` を追加しないでください（二重アクティベーションの原因になります）。

手動で有効化する場合:
```powershell
cd C:\GeminiCLI\TEST\keibabook
.\.venv\Scripts\Activate.ps1
```

### 🏁 アプリ起動スクリプト

Windows PowerShell:
```powershell
./scripts/run_nicegui.sh
```

バッチファイル:
```cmd
scripts/run_nicegui.sh
```

どちらも:
- `.venv` を有効化
- `python -m app_nicegui` を起動
- ブラウザを自動で開く

### 🖱 Windows: デスクトップショートカット作成

簡単に起動したい場合は、以前は `create_shortcut.bat` によるショートカット作成がありましたが、現在はアーカイブされています。Windowsでショートカットを作成するには `scripts/create_console_shortcut.ps1` を使用してください（PowerShellを管理者権限で実行し、仮想環境をアクティベートしてから実行）。

```powershell
.\scripts\create_console_shortcut.ps1
```

デスクトップに `KeibaBook Start` ショートカットが作成されます。タスクバーにピン留めすると1クリックで起動できます。

### 🐧 Linux (Zorin/Ubuntu) - 起動ショートカットと推奨起動法

Linux (Zorin/Ubuntu) で UI を起動する場合の推奨方法:

- 安全に起動（4GB メモリ上限、仮想環境有効化）:
```
./scripts/run_nicegui.sh
```

- デスクトップショートカットの作成:
```
./scripts/create_desktop_shortcut_linux.sh
# ファイルマネージャにデスクトップが表示されていれば、ショートカットが作成されます。
```

---

## 📦 移行済み機能 (keiba-ai へ)
一部の分析/UI機能は keiba-ai プロジェクトに移行しました。KeibaBook はスクレイピング & 出力に集中します。
- トラックバイアス解析 (TrackBias)
- レコメンド / ランキング / 穴馬検出 (Recommender, HorseRanker, UpsetDetector)
- 調教評価 UI / 詳細解析 (Training Evaluation)
- オッズ監視 / 監査ツール (cli_minimal_odds 等)

移行先: migration/to_keiba_ai/ を参照してください。


## 🔧 Configuration

- `special_fetch_grades`: Optional comma-separated list of race grades to limit heavy special page fetches (e.g., "GI,G1"). If omitted, special feature pages are fetched according to the default graded-race logic.
- `fetch_daily_special_pages`: If True, also fetch daily special pages (一覧)

## 🧠 Memory Safety / Watchdog

This project can run heavy scraping tasks (Playwright/Chromium, large Pandas loads) that may cause high memory usage. Suggested options to mitigate OOM:

- Per-process limits: use `prlimit` or `setrlimit` to set an RLIMIT_AS/virtual memory limit for a process. Example:

```bash
# set a 6GB address space limit for a command
prlimit --as=6G -- python scripts/run_scraper.py ...
```

- systemd / cgroup: run processes under a systemd slice or transient unit and set a memory cap:

```bash
# transient unit; MemoryMax sets a hard limit
systemd-run --scope --unit=keibabook-scrape --property=MemoryMax=6G -- python scripts/run_scraper.py ...
```

 - Use the repository's `scripts/watchdog_mem.py` (or legacy `scripts/memory_watchdog.py` / `scripts/mem_watchdog.py`) as a last-resort monitor. It watches overall memory usage and gently SIGTERM/SIGKILL top consumers when thresholds are exceeded. An example systemd transient unit is provided in `scripts/watchdog_mem.service.example`.

 ```bash
 # run as a background watcher (adjust thresholds to taste)
 python scripts/watchdog_mem.py --system-threshold 85 --max-kill 1 --interval 2 --grace 8 &
# recommended threshold: 85%
 ```

 # Example using the Python `run_with_mem_limit.py` helper to run a command with a memory limit:
 ```bash
 ./scripts/run_scraper_with_limit.sh --race_id=20251206...
# recommended per-process Memory limit: 4GB for scrape_worker
 ```

- For WSL: increase swap in `.wslconfig` and restart WSL (`wsl --shutdown`). Example:

```
[wsl2]
memory=6GB
swap=4GB
```

Use conservative parallelism and avoid loading huge datasets into memory in one shot. Prioritize streaming/chunked processing.

See also: `docs/memory_management.md` for rollback steps and deeper guidance.

- A small wrapper `scripts/run_with_memlimit.sh` is provided to run a command under `prlimit`:

```bash
# Example: limit to 6G AS for the scrape worker
./scripts/run_with_memlimit.sh 6G -- python scripts/run_scraper.py --race_id=20251206... 
```


## 📁 プロジェクト構成

```
keibabook/
├── app_nicegui.py            # NiceGUI UI (Streamlit archived)
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
- ✅ 馬柱（過去3走）取得: ポリシーにより削除済み（取得しません）。
- ✅ JRAリアルタイムオッズ取得 (オプション: `skip_realtime_odds=True` で無効化可能。デフォルトは無効に設定されています。)
- ❌ 直前情報（ギリギリ/パドック）: ポリシーにより収集しません（コードから削除済み）。
- ✅ CSV DB保存（重複チェック付き）
- ✅ AI用JSON出力
- ✅ NiceGUI UI (default; Streamlit archived)

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
 - Individual horse detail pages are not opened by the scraper by default (config: `skip_individual_pages`, default True) to reduce load and keep scraping lightweight.
 - Training data is retrieved for both JRA and NAR races where available (the scraper attempts to fetch `{base_url}/cyokyo/0/<race_id>` for both types).

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