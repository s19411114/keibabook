Category: Operational
Status: Active

# 🤖 AIエージェント向け作業ルール

## ⚠️ 絶対に守るべきルール

### 1. 作業環境

**必ず以下の環境で作業してください:**

| 項目 | 値 |
|------|------|
| 作業ディレクトリ | `~/keibabook` またはワークスペースルート |
| Python環境 | `.venv` (Python 3.12) |
| エディタ | VS Code (Remote WSL/WSL2 推奨) |

> ❌ **禁止**: WSL・Docker の使用

### 2. 作業開始時の確認コマンド

```bash
# 必ず最初に実行
pwd  # ワークスペースルートであることを確認
source .venv/bin/activate
which python  # .venvのpythonが表示されるべき
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
- `docs/archived/archived-HANDOVER_CLAUDE_HAIKU.md` - 過去の開発履歴と参考URL（アーカイブ）

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

```bash
cd ~/keibabook
source .venv/bin/activate
python run_scraper.py
```

### Streamlit起動

```bash
cd ~/keibabook
source .venv/bin/activate
python -m app_nicegui
```

または起動スクリプト:
```powershell
./scripts/run_nicegui.sh
```

### テスト実行

```bash
cd ~/keibabook
source .venv/bin/activate
pytest tests/
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

## 📌 ドキュメント運用ルール（重要）
1. すべてのバグ報告・タスク・設計変更・改善提案は `docs/ISSUES_MASTER.md` に記載してください。
2. 新しい課題を追加する場合は `カテゴリ/短い見出し` を先頭にし、`reporter:` `status:` `priority:` を明記してください。
3. 完了した課題は `scripts/extract_completed_from_issues_master.py` を使用して個別セクションとして抽出・アーカイブしてください。既定では完了タスクは `docs/archived/completed_issues.md` にまとめて追記されます。個別ファイル化する場合は `--separate` オプションを指定してください。手順:
	 1. `python scripts/extract_completed_from_issues_master.py`（dry-run; 検出結果を表示します）
	 2. `python scripts/extract_completed_from_issues_master.py --confirm`（検出された完了セクションを `docs/archived/issues_master` に移し、`PROJECT_LOG.md` に追記）
	 3. 重要な決定や移行理由は `PROJECT_LOG.md` に書き残してください。
  
    - CI: `Weekly Archive Dry-Run` workflow runs weekly and opens an issue when it detects completed sections. Review the issue and run the `Manual Archive` workflow via the Actions page to perform `--confirm`.
4. `implementation_plan.md.resolved` の内容は `docs/ISSUES_MASTER.md` にマージされ、過去の計画は `docs/archived/` に移してください。
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