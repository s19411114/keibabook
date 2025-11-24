# 🐎 KeibaBook スクレイパー

競馬ブックから出馬表・調教・血統・コメントデータを取得するスクレイパー

---

## ⚡ クイックスタート（必読）

> **注意**: 今後はDockerを開発の標準ワークフローとします。ローカルの `venv` 手順は `LEGACY_VENV.md` のみに残し、通常は Docker を使用してください。

> 📘 **詳細な手順書（統合）**: [DEV_GUIDE.md](DEV_GUIDE.md) - Docker-first の開発手順（公式）

**セキュリティ**: 認証情報は `config/settings.yml` に書き込まないでください。`LOGIN_ID` / `LOGIN_PASSWORD` を環境変数で渡すことを推奨します。

### 🔧 初回セットアップ（1回のみ｜推奨: Docker）

```bash
cd /mnt/c/GeminiCLI/TEST/keibabook
# 推奨: Docker (WSL/Ubuntu から起動)
./docker-start.sh
```

### 🚀 作業開始コマンド（毎回実行｜Docker推奨）

```bash
cd /mnt/c/GeminiCLI/TEST/keibabook
docker-compose exec app bash
```

### 🧭 旧来の仮想環境（Legacy: 必要ならこちら）

Dockerを使わない場合に備え、従来の仮想環境手順は `LEGACY_VENV.md` にまとめています。通常は Docker を使ってください。

> 詳細手順は `DEV_GUIDE.md` を参照してください。

```bash
# 旧来: 仮想環境を使う場合
cd /mnt/c/GeminiCLI/TEST/keibabook
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
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

### 🐛 トラブルシューティング

**推奨**: Dockerを使っている場合はコンテナ内でコマンドを実行してください。例:

```bash
docker-compose exec app bash
pip install -r requirements.txt
```

### ModuleNotFoundError (Legacy: venv を使う場合のみ)
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
- **`WORKFLOW.md`** - 開発ワークフロー統合版（Git管理、トラブル対応）⭐
- `ARCHITECTURE.md` - システムアーキテクチャ
- `DEVELOPMENT_ROADMAP.md` - 開発ロードマップ
- `PROJECT_LOG.md` - 詳細な開発履歴

### docs/ フォルダ
- `docs/COOKIE_EXPORT_GUIDE.md` - Cookie取得手順
- `docs/LOCAL_RACING_GUIDE.md` - 地方競馬対応ガイド
- `docs/ODDS_FETCHER_GUIDE.md` - オッズ取得ガイド
- `docs/VENUE_GUIDE.md` - 会場コード一覧
