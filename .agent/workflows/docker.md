---
description: Docker環境の起動と使用方法
---

# Docker環境ワークフロー

このプロジェクトはDocker Compose環境を使用します。

## 🚀 起動方法

### Windows から起動

// turbo
```cmd
cd c:\GeminiCLI\TEST\keibabook
docker-start.bat
```

### WSL から起動

// turbo
```bash
cd /mnt/c/GeminiCLI/TEST/keibabook
chmod +x docker-start.sh
./docker-start.sh
```

## 💻 コンテナ内で作業

### コンテナに入る

// turbo
```bash
docker-compose exec app bash
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

## 🔧 メンテナンス

### 依存関係を追加した場合

1. `requirements.txt` を編集
2. イメージを再ビルド:

// turbo
```bash
docker-compose build
```

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

## 📚 詳細ドキュメント

詳細は [DOCKER_SETUP.md](../DOCKER_SETUP.md) を参照してください。
