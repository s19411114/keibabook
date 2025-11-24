# 🎯 エージェント引き継ぎガイド

## 📋 プロジェクト概要

競馬予想データスクレイピング＆分析アプリケーション（KeibaBook Scraper）

---

## 🐳 開発環境（概要）

このプロジェクトは Docker Compose を使用します。詳細・手順は `DEV_GUIDE.md` を参照してください。

```bash
# WSL (推奨)
./docker-start.sh

# Windows (代替)
docker-start.bat
```

### 詳細

詳細は `DOCKER_SETUP.md` と `DEV_GUIDE.md` を参照してください。

---

## ⚠️ 重要な注意事項

### Docker環境について

1. **venvは使用しない** - Dockerが独自の環境を持っています
2. **依存関係はrequirements.txt** - 追加後は `docker-compose build`
3. **ファイル変更は自動同期** - コンテナ内外で即座に反映

### AIエージェントへの指示

```
このプロジェクトはDocker環境を使用しています。

- 起動: docker-start.bat または ./docker-start.sh
- 作業: docker-compose exec app bash でコンテナに入る
- venvは触らない（Docker独自の環境を使用）

詳細は DOCKER_SETUP.md と .agent/workflows/docker.md を参照。
```

---

## 📁 プロジェクト構造

```
keibabook/
├── Dockerfile              # Docker環境定義
├── docker-compose.yml      # サービス定義
├── docker-start.sh         # WSL起動スクリプト
├── docker-start.bat        # Windows起動スクリプト
├── DOCKER_SETUP.md         # Docker完全ガイド
├── src/                    # ソースコード
│   ├── scrapers/          # スクレイパー
│   └── utils/             # ユーティリティ
├── app.py                  # Streamlit UI
├── requirements.txt        # Python依存関係
└── .agent/workflows/       # ワークフロー定義
```

---

## 🚀 よく使うコマンド

### コンテナ操作

```bash
# 起動
docker-compose up -d

# コンテナに入る
docker-compose exec app bash

# 停止
docker-compose down

# ログ確認
docker-compose logs -f
```

### アプリケーション

```bash
# スクレイピング
python run_scraper.py

# Streamlit起動
streamlit run app.py

# テスト実行
pytest tests/
```

---

## 📚 関連ドキュメント

- [README.md](README.md) - プロジェクト概要
- [DOCKER_SETUP.md](DOCKER_SETUP.md) - Docker環境詳細
- [WORKFLOW.md](WORKFLOW.md) - 開発ワークフロー
- [ARCHITECTURE.md](ARCHITECTURE.md) - システム構成
- `.agent/workflows/docker.md` - Dockerワークフロー

---

## 🔧 トラブルシューティング

### ビルドエラー

```bash
docker-compose build --no-cache
```

### コンテナ起動エラー

```bash
docker-compose down -v
docker-compose up -d
```

### ポート競合

`docker-compose.yml` の `ports` セクションを編集

---

**最終更新**: 2025-11-25
