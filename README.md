# 🐎 KeibaBook スクレイパー

競馬ブックから出馬表・調教・血統・コメントデータを取得するスクレイパー

---

## ⚡ クイックスタート（必読）

### 🔧 初回セットアップ（1回のみ）

```bash
cd /mnt/c/GeminiCLI/TEST/keibabook
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

### 🚀 作業開始コマンド（毎回実行）

```bash
cd /mnt/c/GeminiCLI/TEST/keibabook
source venv/bin/activate
```

### 📱 アプリ起動

```bash
# Streamlit GUI（推奨）
streamlit run app.py

# CLI版
python run_scraper.py
```

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
- JRAスケジュール取得の修正（AttributeError解決）
- ログイン認証の修正
- 日付・レース番号の自動推定機能

### 🔄 進行中・未解決
- （ここに現在の課題を記載してください）

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

## 🐛 トラブルシューティング

### ModuleNotFoundError
```bash
source venv/bin/activate  # 仮想環境を有効化
pip install -r requirements.txt
```

### Playwrightブラウザエラー
```bash
playwright install chromium
# または強制再インストール
playwright install --force chromium
```

### ログインエラー
- `cookies.json`が正しく保存されているか確認
- `debug_login.py`でログイン処理をテスト

---

## 📚 詳細ドキュメント（参考）

### ルートレベル
- `ARCHITECTURE.md` - システムアーキテクチャ
- `DEVELOPMENT_ROADMAP.md` - 開発ロードマップ
- `PROJECT_LOG.md` - 詳細な開発履歴

### docs/ フォルダ
- `docs/COOKIE_EXPORT_GUIDE.md` - Cookie取得手順
- `docs/LOCAL_RACING_GUIDE.md` - 地方競馬対応ガイド
- `docs/ODDS_FETCHER_GUIDE.md` - オッズ取得ガイド
- `docs/VENUE_GUIDE.md` - 会場コード一覧
