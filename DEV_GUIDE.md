# Developer Guide (Canonical)

この `DEV_GUIDE.md` はこのリポジトリの**公式な開発手順書**です。
すべての開発者・AIエージェントはここに従って作業してください。

## 1. 開発環境

**推奨環境**: WSL2 (Ubuntu) + Python venv

> ⚠️ **重要**: Dockerは使用しません。WSL上のvenv環境で作業してください。

### 前提条件
- WSL2 (Ubuntu) がインストール済み
- Python 3.12以上
- VS Code + Remote-WSL拡張

## 2. 初回セットアップ

### 2.1 VS Codeで開く

1. VS Codeを起動
2. **左下の緑アイコン**をクリック → 「Connect to WSL」
3. 「Open Folder」→ `/home/<user>/keibabook` を選択

> ⚠️ **Windows側のパス (`/mnt/c/...`) は使用しないでください**
> ファイルI/Oが遅く、Playwrightが不安定になります。

### 2.2 仮想環境のセットアップ

```bash
cd ~/keibabook

# venvが存在しない場合は作成
python3 -m venv venv

# venvをアクティベート
source .venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt

# Playwrightのブラウザをインストール
playwright install chromium
```

## 3. 作業開始（毎回）

```bash
cd ~/keibabook
source .venv/bin/activate
# プロンプトに (.venv) が表示されることを確認
```

## 4. 主要コマンド

```bash
# スクレイピングを実行
python run_scraper.py

# Streamlit GUI を起動
streamlit run app.py

# テストを実行
pytest tests/
```

## 5. 依存関係の変更

1. `requirements.txt` を更新
2. パッケージをインストール:
   ```bash
   pip install -r requirements.txt
   ```

## 6. 🔐 Cookie & 認証情報の運用方針

- 本リポジトリではパスワードを平文保存しない方針です
- `cookies.json` でセッションを保存・再利用可能
- Cookie ファイルは **絶対に** リポジトリにコミットしないでください
- 環境変数 (`LOGIN_ID` / `LOGIN_PASSWORD`) で運用してください

### Cookie を利用するワークフロー:

1. 一度ログインして Cookie を `cookies.json` に保存
2. `COOKIE_FILE` 環境変数でそのファイルを指定
3. Cookie の有効期限が切れたら再ログイン

## 7. Git の安全運用

```bash
# 作業前に必ず確認
git status
git log --oneline -5

# 意味のある単位でコミット
git add .
git commit -m "feat: 機能追加の説明"

# トラブル時
git stash  # 一時退避
git reset --hard <commit>  # 特定コミットに戻す
```

## 8. トラブルシューティング

### ModuleNotFoundError
```bash
pip install -r requirements.txt
```

### Playwrightブラウザがない
```bash
playwright install chromium
```

### 403/429 エラー
- レート制限を下げる
- Cookie を更新
- 重複チェックを有効にする

## 9. ドキュメント構造

- `DEV_GUIDE.md` - 主要な手順書（このファイル）
- `AGENT_RULES.md` - AIエージェント向けルール
- `HANDOVER.md` - 引き継ぎ概要
- `README.md` - プロジェクト概要

---

**最終更新**: 2025-11-27
