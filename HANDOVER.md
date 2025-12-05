# 🎯 エージェント引き継ぎガイド

## 🚨 最初に読むべきファイル

> **重要**: 作業開始前に必ず [`AGENT_RULES.md`](AGENT_RULES.md) を確認してください。

## 📋 プロジェクト概要

競馬予想データスクレイピング＆分析アプリケーション（KeibaBook Scraper）

---

## 🐍 開発環境

**Windows + Python 3.12 + `.venv` を使用します。**

### 作業開始

```powershell
cd C:\GeminiCLI\TEST\keibabook
.\.venv\Scripts\Activate.ps1
```

### 詳細

詳細は `DEV_GUIDE.md` を参照してください。

---

## ⚠️ 重要な注意事項

### 環境について

1. **必ず `C:\GeminiCLI\TEST\keibabook` で作業**
2. **`.venv`をアクティベート** - `.\.venv\Scripts\Activate.ps1`
3. **WSL・Dockerは使用しない**

### AIエージェントへの指示

```
このプロジェクトはWindows + Python 3.12 + .venv環境を使用しています。

- 作業ディレクトリ: C:\GeminiCLI\TEST\keibabook
- Python環境: .\.venv\Scripts\Activate.ps1
- WSL・Dockerは使用しない

詳細は AGENT_RULES.md と DEV_GUIDE.md を参照。
```

---

## 📁 プロジェクト構造

```
C:\GeminiCLI\TEST\keibabook\
├── .venv\              # Python仮想環境 (Python 3.12)
├── src\                # ソースコード
│   ├── scrapers\      # スクレイパー
│   └── utils\         # ユーティリティ
├── app.py             # Streamlit UI
├── requirements.txt   # Python依存関係
└── config\            # 設定ファイル
```

---

## 🚀 よく使うコマンド

```powershell
# .venvアクティベート
.\.venv\Scripts\Activate.ps1

# スクレイピング
python run_scraper.py

# Streamlit起動
streamlit run app.py
# または
.\scripts\start_streamlit_win.ps1

# テスト実行
pytest tests\
```

---

## 📚 関連ドキュメント

- [AGENT_RULES.md](AGENT_RULES.md) - AIエージェント向けルール
- [DEV_GUIDE.md](DEV_GUIDE.md) - 開発手順書
- [README.md](README.md) - プロジェクト概要

---

## 🔄 最近の変更 (2025-11-30)

### トラックバイアス分析タブの実装
`app.py` のメンテナンス性を向上させるため、トラックバイアス分析タブ (tab3) をモジュール化しました。

- **`src/ui/track_bias_tab.py`**: tab3の全ロジック（データ取得、分析、表示）を含む新しいモジュール。
- **`app.py`**: tab3の実装を `render_track_bias_tab` 関数の呼び出しのみに簡素化。

### 次のステップ
- モジュール化されたtab3の動作確認
- 他のタブ（tab4, tab5）のモジュール化検討

---

**最終更新**: 2025-11-30
