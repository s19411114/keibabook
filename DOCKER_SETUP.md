# 🐳 Docker環境セットアップガイド

## 📋 概要

このプロジェクトはDocker Composeを使用した開発環境を提供します。
**エージェント交代時も、このドキュメントに従えば誰でも同じ環境を構築できます。**

---

## 🚀 クイックスタート

> [!IMPORTANT]
> **パフォーマンス重視**: Docker は **WSL (Ubuntu) から起動** することを強く推奨します。
> Windows から直接起動すると、ファイルI/Oが非常に遅くなります。

### 推奨: WSL/Linux から起動

```bash
# WSL (Ubuntu) を起動
wsl

# プロジェクトディレクトリに移動
cd /mnt/c/GeminiCLI/TEST/keibabook

# Docker起動
./docker-start.sh

### 認証情報（環境変数）
このリポジトリでは認証情報は `config/settings.yml` に平文保存しないでください。代わりに以下の方法を推奨します。

1. Docker 実行時に環境変数を設定する
```bash
export LOGIN_ID="your_id"
export LOGIN_PASSWORD="your_password"
```
2. またはプロジェクト直下に `.env` を作成して `docker-compose` に読み込ませる（`.env` は `.gitignore` に追加してください）
```
LOGIN_ID=your_id
LOGIN_PASSWORD=your_password
```
```

### 代替: Windows から起動 (内部的にWSL経由)

```cmd
docker-start.bat
```

ダブルクリックでも起動できます（内部的にWSL経由で実行されます）

> ⚠️ **注意**: Docker 使用時はプロジェクト直下の `venv/` は無視してください。コンテナ内で実行するため、ホストの仮想環境をアクティベートしないでください。

---

## 📦 含まれるもの

### Docker設定ファイル

- **Dockerfile**: Python 3.12 + 全依存関係
- **docker-compose.yml**: サービス定義とボリュームマウント
- **.dockerignore**: ビルドから除外するファイル

### 起動スクリプト

- **docker-start.bat**: Windows用起動スクリプト
- **docker-start.sh**: WSL/Linux用起動スクリプト

---

## 🔧 初回セットアップ

### 1. 前提条件

- Docker Desktop for Windows がインストール済み
- WSL2 が有効化済み
- プロジェクトディレクトリ: `c:\GeminiCLI\TEST\keibabook`

### 2. 起動

#### 方法A: WSLから (推奨 - 高速)

```bash
# WSLを起動
wsl

# プロジェクトディレクトリに移動
cd /mnt/c/GeminiCLI/TEST/keibabook

# 実行権限を付与 (初回のみ)
chmod +x docker-start.sh

# Docker起動
./docker-start.sh
```

#### 方法B: Windowsから (WSL経由で実行)

```cmd
cd c:\GeminiCLI\TEST\keibabook
docker-start.bat
```

### 3. 初回ビルド

初回起動時は自動的にDockerイメージをビルドします（5-10分程度）。
以降の起動は数秒で完了します。

---

## 💻 使い方

### コンテナに入る

```bash
docker-compose exec app bash
```

### コンテナ内での作業

```bash
# スクレイピング実行
python run_scraper.py

# Streamlit起動
streamlit run app.py

# テスト実行
pytest tests/
```

### コンテナから出る

```bash
exit
```

### コンテナを停止

```bash
docker-compose down
```

---

## 📂 ディレクトリ構造

```
keibabook/
├── Dockerfile              # Dockerイメージ定義
├── docker-compose.yml      # サービス定義
├── .dockerignore          # ビルド除外ファイル
├── docker-start.sh        # WSL起動スクリプト
├── docker-start.bat       # Windows起動スクリプト
├── requirements.txt       # Python依存関係
├── src/                   # ソースコード (マウント)
├── data/                  # データ (マウント)
└── venv/                  # ※Dockerでは使用しない
```

---

## 🔄 依存関係の管理

### 新しいパッケージを追加する場合

1. `requirements.txt` に追加
2. イメージを再ビルド:
   ```bash
   docker-compose build
   ```

### 現在インストールされているパッケージ

- beautifulsoup4 (bs4)
- playwright
- streamlit
- pandas
- その他 (requirements.txt参照)

**重要**: venvの依存関係は引き継がれません。Dockerは`requirements.txt`から全て再インストールします。

> 補足: Dockerfile には `playwright install chromium` を含めています。ローカルで venv を使って実行する場合のみ、`playwright install chromium` を手動で実行してください。

---

## 🛠️ トラブルシューティング

### ビルドが失敗する

```bash
# キャッシュをクリアして再ビルド
docker-compose build --no-cache
```

### コンテナが起動しない

```bash
# ログを確認
docker-compose logs

# コンテナを完全削除して再起動
docker-compose down -v
docker-compose up -d
```

### ポートが既に使用されている

```bash
# 8501ポートを使用しているプロセスを確認
netstat -ano | findstr :8501

# docker-compose.ymlでポートを変更
ports:
  - "8502:8501"  # 8502に変更
```

---

## 🎯 エージェント引き継ぎ時の手順

### 新しいエージェントへの指示

```
このプロジェクトはDocker Compose環境を使用しています。

1. 起動方法:
   - Windows: docker-start.bat を実行
   - WSL: ./docker-start.sh を実行

2. 作業方法:
   - docker-compose exec app bash でコンテナに入る
   - コンテナ内で開発作業を行う

3. 重要事項:
   - venvは使用しない (Docker独自の環境)
   - 依存関係はrequirements.txtで管理
   - ファイル変更は自動的にホストと同期

詳細は DOCKER_SETUP.md を参照してください。
```

---

## ⚙️ 高度な使い方

### バックグラウンドで起動

```bash
docker-compose up -d
```

### ログを表示

```bash
docker-compose logs -f
```

### 特定のコマンドを実行

```bash
docker-compose exec app python run_scraper.py
```

### イメージを削除

```bash
docker-compose down --rmi all
```

---

## 📝 よくある質問

### Q: venvは削除していいですか?

A: はい。Dockerを使う場合、venvは不要です。
ただし、Docker外でも作業したい場合は残しておいてください。

### Q: requirements.txtを更新したら?

A: `docker-compose build` で再ビルドが必要です。

### Q: データは保持されますか?

A: はい。`data/`フォルダはマウントされているので、
コンテナを削除してもデータは残ります。

### Q: Windowsでも使えますか?

A: はい。`docker-start.bat`を使用してください。
内部的にWSL経由でDockerを起動します。

---

## 🔒 セキュリティ

- **cookies.json**: Gitにコミットしないでください (.gitignoreに追加済み)
- **config/settings.yml**: 認証情報は環境変数で管理することを推奨

---

## 📚 関連ドキュメント

- [WORKFLOW.md](WORKFLOW.md) - 開発ワークフロー
- [README.md](README.md) - プロジェクト概要
- [ARCHITECTURE.md](ARCHITECTURE.md) - システム構成
