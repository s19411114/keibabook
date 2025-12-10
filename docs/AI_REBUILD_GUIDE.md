Category: Guide
Status: Active

# AI Rebuild Guide — KeibaBook

目的
- このドキュメントは、別のAI（または人）が1日で動く最小限のクローニングを行い、継続的に改良できるようにすることを目的とします。
- 重要な設計上の注意点、環境設定、テスト仕様、反省点（失敗と改善点）、そして実行プランを含みます。

スコープ
- まずは「スクレイピング」コアを再構築：`run_scraper.py` の動作、主要スクレイパー、`scripts/ensure_venv.sh` の自動化、最小 Streamlit UI の起動コマンドまでを対象とします。

前提（Constraints）
- Python 3.12 を想定
- Playwright を利用（Chromium）
- OS: Linux (WSL2 推奨) および Windows の PowerShell をサポート
- 仮想環境: `.venv` を使い VS Code の自動有効化に依存する（手動アクティベートは避ける）

設計上の注意点（必読）
- 仮想環境の扱い
  - VS Code の `python.terminal.activateEnvironment: true` を有効にし、`~/.bashrc` 等に `source .venv/bin/activate` を書かないこと。二重起動で `(.venv)` が重複するため。
  - 開発ドキュメントやサンプルでは `python3 -m venv .venv` を使うこと。
- VS Code の設定・ターミナルプロファイル
  - 統合ターミナルプロファイルに `args` で `source .venv` を入れず、VS Code に任せる。
  - `.vscode/settings.json` に `"python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"` を指定。
- ファイル/ディレクトリ構成
  - `src/` に全ソース、`scripts/` に起動や補助スクリプト、`docs/` に設計・運用ドキュメント。
  - `data/` は実行時データ、`config/settings.yml` は環境固有の設定（認証情報は .env か環境変数で）
- サードパーティライブラリ・依存管理
  - `requirements.txt` と `dev-requirements.txt` を分離
  - 依存導入は `scripts/ensure_venv.sh` で再現可能にする
- Playwright とブラウザ
  - `playwright install chromium` は CI や初回セットアップで必須
  - ヘッドレスとヘッドフルのオプションで起動を切り替えられるようにする
- Rate limiting・礼節
  - レスポンスの待ち時間とリトライ戦略を明示。JRA等スクレイピング先のポリシーに準拠すること。
- 監視・メモリ
  - 大きなデータ処理はメモリ消費に注意し、`prlimit` や systemd を推奨する。`scripts/watchdog_mem.py` を有効に。プロセス単位のメモリ上限を設定する
- エラーハンドリングとリトライ
  - ネットワーク系は指数バックオフの自動リトライ
  - 明快なログとエラーステータス（100, 200, 429, 403 など）を記録
- テスト
  - ユニットテスト（`tests/`）を整備して基本の I/O を保護する
  - API やスクレイピング対象が動く場合は E2E テストを用意
  - Playwright は CI でヘッドレス実行を必須化
- パラメータと設定の分離
  - `config/settings.yml` に統合し、秘密情報は環境変数 `LOGIN_ID`, `LOGIN_PASSWORD`, `COOKIE_FILE` で渡す
- ロギング
  - アプリ・ライブラリ両方で構成可能なロギング（ファイル/STDOUT）を持つ
  - ログローテーションの指示を用意
- 再現性
  - `scripts/ensure_venv.sh` を使って `requirements.txt` をインストールできること
  - すべてのコマンドが `scripts/` のラッパーから呼べること

反省点（改善すべき点）
- ドキュメントの散逸
  - 同じ指示が README/DEV_GUIDE/スクリプト/README に分散し、古い記述が残っていた
  - 解決: 操作手順は `DEV_GUIDE.md` に一本化し、README には簡潔な概要のみ残す
- VS Code 設定の二重化
  - `terminal.integrated.profiles.linux` と `python.terminal.activateEnvironment` の両方で有効化していた
  - 解決: どちらか一方（VS Code の `python.terminal.activateEnvironment`）に統一
- 起動コマンドの不整合
  - `scripts` の起動時と README の例でパスが混在（`venv` / `.venv` や Windows / Linux）
  - 解決: 一貫したコマンドと、OS別の例を必ず用意
- テスト不足
  - Playwright の E2E、長時間実行のメモリテストが不足
  - 解決: CI への追加と Canary テスト追加
- 設定のハードコード
  - `.vscode/settings.json` や `keibabook.code-workspace` に OS 固有の絶対パスが残っていることがあった
  - 解決: 相対パス化と `%USERPROFILE%` / `${workspaceFolder}` を使う
- コミット不要ファイル・個人データの混入
  - `cookies.json` をコミットしない運用が徹底されていなかった
  - 解決: gitignored、`AGENT_RULES.md` に厳格化すること

1日でやるための「AIによる再構築」プラン（短期・MVP）
- 目標（MVP）: `python run_scraper.py` が `--race-id` あるいは `--playwright` オプションで最小限動く。CI ワークフローで `pytest` と Playwright の `chromium` インストールまでをパスする

時間配分（1日=8時間）
- 0.5h: リポジトリのスナップショット・既存ドキュメントと設定を読み込む
- 0.5h: 環境整備（`.venv` 作成、`requirements` をインストール）
- 1.0h: `run_scraper.py` の最小構成を検証し、`scripts/ensure_venv.sh` を実行
- 2.5h: `src/scrapers` の主要ファイルを抽出し、簡易実行パスを作る（`keibabook.py`, `jra_schedule.py`, `jra_odds.py`）
- 1.0h: E2E の Playwright スクリプトを準備（ヘッドレス）
- 1.0h: テスト（pytest）を作る—ユニットテスト + Playwright smoke test
- 1.0h: 説明ドキュメントとハンドオーバー（このガイドを拡張）

AI向け作業ブレイクダウン（実行可能な TODO）
- STEP 0: リポジトリの読み込みと依存解析
  - `grep -R "def main\(|if __name__ == '__main__'" -n` でエントリポイントを特定
- STEP 1: 環境生成・設定
  - `.venv` と `requirements` の自動セットアップを確認
  - `.vscode/settings.json` で `python.terminal.activateEnvironment` を `true`、`terminal.integrated.profiles.linux` の `args` を削除
- STEP 2: 最小スクレイピングランナーの作成
  - `run_scraper.py` の主要引数（`--race_id`, `--dry-run`, `--headful`）をサポート
  - サンプル `race_id` を用意し、`scripts/run_scraper_with_limit.sh` でメモリ制限を適用して起動
- STEP 3: Playwright の基本操作を抽出
  - `login`、`fetch_page` を独立した小さな関数に分割
  - `playwright` を使うコードは `tests/e2e` でヘッドレス実行可能に
- STEP 4: Basic Tests
  - `pytest tests/test_scraper_core.py` を追加。`requests` をモックして `keibabook` のインターフェースを検証
  - Playwright smoke test を `tests/e2e/test_playwright_smoke.py` に追加（`chromium` ヘッドレスで1ページのタイトルを取得する程度）
- STEP 5: Acceptance Criteria
  - `python run_scraper.py --race-id=20251124_tokyo11R --dry-run` が非ゼロを返さない（dry-run が成功する）
  - `pytest` がすべてパスする
  - `playwright install chromium` が成功して smoke test をパス

Handover チェックリスト（AI が行動を完結させるため）
- [ ] `.venv` と `requirements` を自動でセットアップして `run_scraper.py` が起動する
- [ ] `python3 -c 'import playwright'` が CIで動く
- [ ] `tests/` の pytest と e2e が CI で通る（ヘッドレス）
- [ ] `scripts/ensure_venv.sh` が `DEMO` スクリプトとして動く
- [ ] VS Code 設定が `python.terminal.activateEnvironment` で統一されている

AIへの特記事項
- 自動生成コードはユニットテスト（`pytest`）と smoke test がないとマージしない
- 設定・環境ファイルは OS によらず相対パスを使う。Windows の Powershell 用は `scripts/` に別のスクリプトを用意
- 秘密情報は `.env` と `environment variables` で取り扱う

最後に：チェックサンプル（受け入れ）
- すべての実装は `tests/` の pytest によってカバーされている
- `run_scraper.py --race-id <sample>` を `--dry-run` で実行でき、ログファイルが `logs/` に生成される
- `docs/AI_REBUILD_GUIDE.md` に記載された手順で再構築ができる

---

このドキュメントをもとに、別の AI に再生成タスクを任せる準備が整っています。ご希望であれば、今すぐ AI のタスクリスト (小さなコミット単位) を生成して 1日 (8時間) での目標に沿った差分を作らせるスケジュールを出します。