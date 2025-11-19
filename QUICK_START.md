# クイックスタートガイド

## 開発時間見積もり

**実装完了まで: 約1日（集中作業）**

- Streamlit GUI: 2-3時間
- CSV DB + 重複チェック: 2-3時間  
- 馬柱パーサー改善: 2-3時間
- エラーハンドリング: 1-2時間
- 統合テスト: 1-2時間

## セットアップ（5分）

### 1. 仮想環境の作成（WSL/Ubuntu推奨）

```bash
cd /mnt/c/GeminiCLI/TEST/keibabook
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

### 2. 動作確認

```bash
# CLI版のテスト実行
python run_scraper.py

# Streamlit GUIの起動
streamlit run app.py
```

ブラウザで `http://localhost:8501` が開きます。

## 使い方

### Streamlit GUI（推奨）

1. `streamlit run app.py` で起動
2. ブラウザで操作画面が開く
3. 「スクレイピング」タブでレース情報を入力
4. 「🚀 スクレイピング開始」ボタンをクリック
5. 進捗バーで進行状況を確認
6. 「データ確認」タブで結果を確認

### CLI版

```bash
# config/settings.yml の設定に従って実行
python run_scraper.py
```

## データ保存先

- **CSV DB**: `data/db/` ディレクトリ
  - `races.csv`: レース基本情報
  - `horses.csv`: 馬情報
  - `url_log.csv`: 取得済みURLログ（重複チェック用）
  
- **JSON**: `data/` ディレクトリ
  - `{race_key}.json`: レースごとの詳細JSON
  - `json/{race_id}.json`: AI用JSON（加工済み）

## 重複チェック機能

- 一度取得したURLは自動的にスキップされます
- `data/db/url_log.csv` で取得履歴を確認可能
- Streamlit GUIで重複チェックのON/OFFを切り替え可能

## 次のステップ

1. **馬柱HTMLの構造確認**: `debug_page.html` を確認して、実際のHTML構造に合わせてパーサーを調整
2. **定期実行設定**: `schedule` や `apscheduler` を使って朝の自動実行を設定
3. **中央・地方競馬対応**: UIの分岐を実装（現在は準備済み）

## トラブルシューティング

詳細は `SETUP.md` を参照してください。

