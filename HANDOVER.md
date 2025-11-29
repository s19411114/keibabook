# 🎯 エージェント引き継ぎガイド

## 🚨 最初に読むべきファイル

> **重要**: 作業開始前に必ず [`AGENT_RULES.md`](AGENT_RULES.md) を確認してください。

## 📋 プロジェクト概要

競馬予想データスクレイピング＆分析アプリケーション（KeibaBook Scraper）

---

## 🐍 開発環境

**WSL (Ubuntu) + Python venv を使用します。**

### 作業開始

```bash
cd ~/keibabook
source venv/bin/activate
```

### 詳細

詳細は `DEV_GUIDE.md` を参照してください。

---

## ⚠️ 重要な注意事項

### 環境について

1. **必ず `~/keibabook` で作業** - `/mnt/c/...` は使用しない
2. **venvをアクティベート** - `source venv/bin/activate`
3. **Dockerは使用しない**

### AIエージェントへの指示

```
このプロジェクトはWSL + venv環境を使用しています。

- 作業ディレクトリ: ~/keibabook
- Python環境: source venv/bin/activate
- Dockerは使用しない

詳細は AGENT_RULES.md と DEV_GUIDE.md を参照。
```

---

## 📁 プロジェクト構造

```
~/keibabook/
├── venv/               # Python仮想環境
├── src/                # ソースコード
│   ├── scrapers/      # スクレイパー
│   └── utils/         # ユーティリティ
├── app.py             # Streamlit UI
├── requirements.txt   # Python依存関係
└── config/            # 設定ファイル
```

---

## 🚀 よく使うコマンド

```bash
# venvアクティベート
source venv/bin/activate

# スクレイピング
python run_scraper.py

# Streamlit起動
streamlit run app.py

# テスト実行
pytest tests/
```

---

## 📚 関連ドキュメント

- [AGENT_RULES.md](AGENT_RULES.md) - AIエージェント向けルール
- [DEV_GUIDE.md](DEV_GUIDE.md) - 開発手順書
- [README.md](README.md) - プロジェクト概要

---

**最終更新**: 2025-11-27
