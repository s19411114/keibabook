# 🤖 AIエージェント向け作業ルール

## ⚠️ 絶対に守るべきルール

### 1. 作業環境

**必ず以下の環境で作業してください:**

| 項目 | 値 |
|------|------|
| 作業ディレクトリ | `C:\GeminiCLI\TEST\keibabook` |
| Python環境 | `.venv` (Python 3.12) |
| エディタ | VS Code (Windows) |

> ❌ **禁止**: WSL・Docker の使用

### 2. 作業開始時の確認コマンド

```powershell
# 必ず最初に実行
pwd  # C:\GeminiCLI\TEST\keibabook であることを確認
.\.venv\Scripts\Activate.ps1
Get-Command python | Select-Object -ExpandProperty Source  # .venv内のPythonが表示されるべき
```

### 3. 禁止事項

- ❌ **.venvをアクティベートせずにPythonを実行しない**
- ❌ **`pip install` をシステムPythonに直接実行しない**
- ❌ **環境を確認せずにスクリプトを実行しない**
- ❌ **WSL・Dockerコマンドを使用しない**

### 4. 🚫 削除禁止リスト

以下のファイル・ディレクトリは**絶対に削除してはいけません**：

**ドキュメント（参考資料として保存）:**
- `docs/DATA_SOURCES.md` - データソースURL一覧（JRA・地方競馬の公式URL等）
- `docs/MULTI_SOURCE_STRATEGY.md` - データ取得戦略
- `docs/*.md` - すべてのドキュメント
- `README.md`, `WORKFLOW.md`, `HANDOVER.md`
- `issues/HANDOVER_CLAUDE_HAIKU.md` - 過去の開発履歴と参考URL

**設定・認証:**
- `.vscode/settings.json` - VS Code設定
- `config/settings.yml` - アプリケーション設定
- `cookies.json` - 認証情報（有効期限: 2026-11-25）

**データディレクトリ:**
- `data/` - 取得済みレースデータ
- `pedigree_store/` - 血統データ
- `raw_html/` - デバッグ用HTML

**URLや参考情報を削除する前に:**
1. そのURLが参考資料として保存されているか確認
2. 削除が必要な場合は `docs/` に移動して出典を明記
3. 削除/移動の理由を `PROJECT_LOG.md` に記録

---

## 📁 プロジェクト構造

```
C:\GeminiCLI\TEST\keibabook\
├── .venv\              # Python仮想環境 (Python 3.12)
├── src\                # ソースコード
│   ├── scrapers\      # スクレイパー
│   └── utils\         # ユーティリティ
├── data\              # 出力データ
├── config\            # 設定ファイル
├── tests\             # テストコード
├── app.py             # Streamlit UI
├── run_scraper.py     # CLIスクレイパー
└── requirements.txt   # 依存関係
```

---

## 🔧 よく使うコマンド

### スクレイピング

```powershell
cd C:\GeminiCLI\TEST\keibabook
.\.venv\Scripts\Activate.ps1
python run_scraper.py
```

### Streamlit起動

```powershell
cd C:\GeminiCLI\TEST\keibabook
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

または起動スクリプト:
```powershell
.\scripts\start_streamlit_win.ps1
```

### テスト実行

```powershell
cd C:\GeminiCLI\TEST\keibabook
.\.venv\Scripts\Activate.ps1
pytest tests\
```

### 依存関係の更新

```powershell
pip install -r requirements.txt
```

---

## 🔧 トラブル発生時

### 症状: Pythonモジュールが見つからない

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 症状: Playwrightがエラー

```powershell
playwright install chromium
```

---

## 📝 エージェント引き継ぎ時のチェックリスト

新しいエージェントは以下を最初に確認:

- [ ] `pwd` で `C:\GeminiCLI\TEST\keibabook` にいることを確認
- [ ] `.\.venv\Scripts\Activate.ps1` を実行
- [ ] `Get-Command python` で .venv内のPythonを確認
- [ ] このファイル (`AGENT_RULES.md`) を読む
- [ ] `DEV_GUIDE.md` を参照

---

## 📚 関連ドキュメント

- [DEV_GUIDE.md](DEV_GUIDE.md) - 開発手順書（公式）
- [HANDOVER.md](HANDOVER.md) - 引き継ぎ概要
- [README.md](README.md) - プロジェクト概要

---

**作成日**: 2025-11-27
**目的**: エージェント間での環境トラブル防止
