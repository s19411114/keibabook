# 🔄 開発ワークフロー（統合版）

## 📋 目次
1. [作業開始手順](#作業開始手順)
2. [Git安全運用](#git安全運用)
3. [スクレイピング実行](#スクレイピング実行)
4. [トラブル時の復旧](#トラブル時の復旧)

---

## 🚀 作業開始手順

**環境**: Windows + Python 3.12 + `.venv`

### 毎回実行するコマンド
```powershell
# プロジェクトフォルダに移動
cd C:\GeminiCLI\TEST\keibabook

# 仮想環境を有効化（VS Codeなら自動）
.\.venv\Scripts\Activate.ps1

# 現在のブランチとステータスを確認
git status
git log --oneline -5
```

### 初回セットアップ（1回のみ）
```powershell
cd C:\GeminiCLI\TEST\keibabook
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

---

## 🛡️ Git安全運用

### 作業前：セーフポイント作成
```bash
# 現在の変更を確認
git status
git diff --stat

# 変更をコミット（セーフポイント）
git add -A
git commit -m "wip: セーフポイント - $(date +%Y%m%d_%H%M%S)"

# コミットIDをメモ（念のため）
git log --oneline -1
```

### 作業中：こまめにコミット
```bash
# 意味のある単位でコミット
git add -A
git commit -m "feat: 機能追加の説明"
# または
git commit -m "fix: バグ修正の説明"
# または
git commit -m "wip: 作業中 - 説明"
```

### トラブル時：ロールバック手順

#### 直前のコミットに戻す
```bash
# 変更を破棄して直前のコミットに戻る
git reset --hard HEAD

# 1つ前のコミットに戻る
git reset --hard HEAD~1

# 2つ前のコミットに戻る
git reset --hard HEAD~2
```

#### 特定のコミットに戻す
```bash
# コミット履歴を確認
git log --oneline -10

# 特定のコミットIDに戻る（例: ebffda8）
git reset --hard ebffda8
```

#### 変更を一時退避
```bash
# 現在の変更を退避（コミットせずに保存）
git stash save "作業中の変更を退避"

# 退避した変更を確認
git stash list

# 退避した変更を復元
git stash pop

# 退避した変更を破棄
git stash drop
```

### リモートとの同期
```bash
# リモートにプッシュ（バックアップ）
git push origin feat/agent-run

# リモートから最新を取得
git pull origin feat/agent-run

# 強制プッシュ（ローカルを優先）※注意
git push -f origin feat/agent-run
```

---

## 🕷️ スクレイピング実行

### Streamlit GUI（推奨）
```powershell
cd C:\GeminiCLI\TEST\keibabook
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

または起動スクリプト:
```powershell
.\scripts\start_streamlit_win.ps1
```

### CLI版
```powershell
cd C:\GeminiCLI\TEST\keibabook
.\.venv\Scripts\Activate.ps1
python run_scraper.py
```

### Cookie更新手順
1. Chrome拡張機能（EditThisCookie等）をインストール
2. https://s.keibabook.co.jp/ にログイン
3. Cookieをエクスポート
4. `cookies.json` として保存

詳細: `docs/COOKIE_EXPORT_GUIDE.md`

---

## 🆘 トラブル時の復旧

### エディタ（Gemini CLI）が制限をかけた場合

#### 症状
- エディタが応答しない
- 処理が途中で止まる
- エラーメッセージが表示される

#### 対処法
1. **現在の作業を保存**
   ```powershell
   # 別のターミナルを開く
   cd C:\GeminiCLI\TEST\keibabook
   git add -A
   git commit -m "emergency: エディタ制限前の緊急保存"
   ```

2. **エディタを再起動**
   - エディタを閉じて再度開く
   - 前回のコミットから続行

3. **最悪の場合：Gitから復旧**
   ```powershell
   # 最新のコミットを確認
   git log --oneline -5
   
   # 特定のコミットに戻る
   git reset --hard <コミットID>
   ```

### スクレイパーがアクセス制限を受けた場合

#### 症状
- 403 Forbidden エラー
- 429 Too Many Requests エラー
- ページが取得できない

#### 対処法
1. **待機時間を長くする**
   - `config/settings.yml` の待機時間を増やす
   - 推奨: 最低10分以上

2. **重複チェックを有効化**
   - 既に取得したデータは再取得しない
   - GUI: 「重複チェックを有効化」にチェック

3. **Cookie を更新**
   - ログイン状態が切れている可能性
   - 上記「Cookie更新手順」を実施

---

## 📝 よく使うGitコマンド早見表

| コマンド | 説明 |
|---------|------|
| `git status` | 現在の状態を確認 |
| `git log --oneline -10` | 最近10件のコミット履歴 |
| `git diff` | 変更内容を確認 |
| `git add -A` | すべての変更をステージング |
| `git commit -m "メッセージ"` | コミット |
| `git reset --hard HEAD` | 変更を破棄 |
| `git reset --hard HEAD~1` | 1つ前に戻る |
| `git stash` | 変更を一時退避 |
| `git stash pop` | 退避した変更を復元 |

---

## 🔗 関連ドキュメント

- `README.md` - プロジェクト概要とクイックスタート
- `ARCHITECTURE.md` - システムアーキテクチャ
- `docs/COOKIE_EXPORT_GUIDE.md` - Cookie取得手順
- `docs/LOCAL_RACING_GUIDE.md` - 地方競馬対応ガイド
