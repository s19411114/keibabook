# Developer Guide (Canonical)

この `DEV_GUIDE.md` はこのリポジトリの**公式な開発手順書**です。
すべての開発者はここに従って作業してください。ドッカー中心のワークフローを採用しています。

## 1. 目的
- このドキュメントは、プロジェクトの初回セットアップから開発・テスト・デプロイまでを包括的にまとめたものです。
- Docker を推奨し、ローカルの `venv` 手順は **互換性・保守用** として `LEGACY_VENV.md` に残しています。

## 2. 推奨ワークフロー（Docker / WSL）

- WSL2（Ubuntu） を有効にしておくこと (Docker Desktop の WSL 統合を利用)
- Docker Desktop がインストール済み
### 前提
- WSL2（Ubuntu） を有効にしておくこと (Docker Desktop の WSL 統合を利用)
- Docker Desktop がインストール済み
- WSL2（Ubuntu） を有効にしておくこと (Docker Desktop の WSL 統合を利用)
- Docker Desktop がインストール済み

### 起動（推奨・WSL）
```bash
# WSL を起動
wsl
cd /mnt/c/GeminiCLI/TEST/keibabook
chmod +x docker-start.sh  # 初回のみ
./docker-start.sh
```

### 認証の取り扱い
このプロジェクトでは `config/settings.yml` にパスワードを平文で残さない方針です。代わりに環境変数で `LOGIN_ID` と `LOGIN_PASSWORD` を渡してください（Docker では `.env` ファイルを使うか、`docker-compose` の `environment` を通して渡します）。

### Windows から起動（代替）
```powershell
cd C:\GeminiCLI\TEST\keibabook
.\docker-start.bat
```

### コンテナに入る
```bash
docker-compose exec app bash
```
## 🔐 Cookie & 認証情報の運用方針

- 本リポジトリではパスワードを `config/settings.yml` に平文保存しない方針です。
- 開発時の利便性のために `cookies.json` のようなファイルでセッションを保存し再利用することは可能です。だたし、以下の点に注意してください:
	- Cookie ファイルは **絶対に** リポジトリにコミットしないでください。
	- `.env` ファイルや環境変数（`LOGIN_ID` / `LOGIN_PASSWORD` / `COOKIE_FILE`）で運用してください。
	- 既にコミット済みの Cookie ファイルがある場合は、以下のコマンドで追跡を解除してください（チームに一報し、必要なら履歴削除の合意を取ってください）。

```pwsh
git rm --cached cookies.json cookies_debug.json || true
git commit -m "chore: remove cookie files from repo and stop tracking"
git push
```

- Cookie を利用するワークフロー:
	1. ローカル環境（Docker あるいは venv）で一度ログイン（`LOGIN_ID`/`LOGIN_PASSWORD` を指定）し、Cookie を `cookies.json` に保存する。
	2. `COOKIE_FILE` 環境変数でそのファイルを指定することで、以後はログインを繰り返さずにスクレイプできます。
	3. Cookie の有効期限が切れた場合は、同じ手順で再ログインしてください。

- もし、追跡済みの Cookie をリポジトリ履歴から完全に消したい場合は、`git filter-repo` などのツールで履歴を消すことができます（履歴改変はチームで合意を取ってから実行してください）。


## 3. コンテナ内での主要コマンド
```bash
# スクレイピングを実行
python run_scraper.py

# Streamlit GUI を起動
streamlit run app.py

# テストを実行
pytest tests/
```

## 4. 依存関係の変更
1. `requirements.txt` を更新
2. イメージの再ビルド
```bash
docker-compose build
```

## 5. Playwright とブラウザ依存性
- Dockerfile は `playwright install chromium` と `playwright install-deps` を含んでいます。
- ローカル（venv）で作業する場合のみ、次を実行してください。
```bash
playwright install chromium
playwright install-deps
```

## 6. LEGACY: 仮想環境 (`venv`)
- Docker を推奨しますが、ローカルで venv を使用する必要がある場合は `LEGACY_VENV.md` を参照してください。

## 7. Git の安全運用（簡易）
- 作業前に必ず `git status` と `git log --oneline -5` を確認
- 意味のある単位でコミット（`wip` など）
- トラブル時は `git stash` または `git reset --hard <commit>` を使用

## 8. トラブルシューティング（よくある事象）
- Playwright ブラウザがない: Docker イメージを再ビルド、またはローカルで `playwright install chromium` を実行
- 403/429 エラー: レートを下げる・Cookie 更新・重複チェックを有効にする
- データが見つからない: `configs/settings.yml` の `output_dir` と `race_id` 等を確認

## 9. ドキュメント構造と責務
- `DEV_GUIDE.md` が主要な手順書です（必ず最新版を参照）
- `DOCKER_SETUP.md`: Docker の詳細手順と環境依存の補足
- `WORKFLOW.md` / `README.md` / `HANDOVER.md`: 高レベルの手順と要点（詳細は `DEV_GUIDE.md` を参照）
- `LEGACY_VENV.md`: 旧来の仮想環境手順（保守用）

---

このファイルは「一本化された」開発手順書です。必要に応じて更新して下さい。

---
**最終更新**: 2025-11-25
