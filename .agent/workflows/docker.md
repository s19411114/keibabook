---
description: Docker環境の起動と使用方法
---

# Docker環境ワークフロー（簡易）

このドキュメントは簡易ガイドです。詳細な手順とトラブルシューティングについては `DEV_GUIDE.md` を参照してください。

## 簡易起動方法（WSL推奨）

```bash
cd /mnt/c/GeminiCLI/TEST/keibabook
./docker-start.sh
```

## コンテナ内での基本操作

```bash
# コンテナに入る
docker-compose exec app bash

# スクレイピング
python run_scraper.py

# Streamlit起動
streamlit run app.py

# テスト実行
pytest tests/
```

### スクレイピング実行

// turbo
```bash
python run_scraper.py
```

### Streamlit起動

// turbo
```bash
streamlit run app.py
```

### テスト実行

// turbo
```bash
pytest tests/
```

## 🛑 終了方法

### コンテナから出る

```bash
exit
```

### コンテナを停止

// turbo
```bash
docker-compose down
```

## メンテナンス

`DOCKER_SETUP.md` に詳細が書かれています。`requirements.txt` を更新した場合は `docker-compose build` を実行してください。

### トラブル時

// turbo
```bash
# ログ確認
docker-compose logs

# 完全リセット
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## ⚠️ 重要事項

- **venvは使用しない**: Dockerが独自の環境を持っています
- **ファイル変更は自動同期**: コンテナ内外で即座に反映
- **データは永続化**: `data/`フォルダは保持されます

## 詳細ドキュメント

詳細が必要な場合は `DEV_GUIDE.md` 及び `DOCKER_SETUP.md` を参照してください。
