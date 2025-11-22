# 開発環境セットアップ手順

## 推奨環境: WSL/Ubuntu

**理由:**
- WindowsとLinuxの両方で動作確認可能
- 仮想環境の管理が安定
- 将来的なデプロイ（Linuxサーバー）に移行しやすい
- パッケージ管理がシンプル

## セットアップ手順

### 1. WSL/Ubuntuで仮想環境を作成

```bash
# プロジェクトディレクトリに移動
cd /mnt/c/GeminiCLI/TEST/keibabook

# 既存の仮想環境がある場合は削除（オプション）
# rm -rf venv

# 新しい仮想環境を作成
python3 -m venv venv

# 仮想環境をアクティベート
source venv/bin/activate

# pipを最新化
pip install --upgrade pip
```

### 2. 依存パッケージのインストール

```bash
# requirements.txtからインストール
pip install -r requirements.txt

# Playwrightブラウザをインストール（重要！）
playwright install chromium
```

### 3. 動作確認

```bash
# スクレイパーのテスト実行
python run_scraper.py

# Streamlitアプリの起動
streamlit run app.py
```

## 仮想環境の管理

### アクティベート（毎回必要）
```bash
cd /mnt/c/GeminiCLI/TEST/keibabook
source venv/bin/activate
```

### 非アクティベート
```bash
deactivate
```

### 仮想環境の再作成が必要な場合
```bash
# 仮想環境を削除
rm -rf venv

# 上記のセットアップ手順を再度実行
```

## トラブルシューティング

### Playwrightブラウザが起動しない
```bash
# ブラウザを再インストール
playwright install --force chromium
```

### パッケージの競合エラー
```bash
# 仮想環境を再作成してクリーンインストール
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Windows側でエディタが仮想環境を認識しない
- VS Code/Cursorは通常、WSLの仮想環境を自動認識します
- 認識されない場合は、エディタのPythonインタープリターを手動で選択：
  - `Ctrl+Shift+P` → "Python: Select Interpreter"
  - `/mnt/c/GeminiCLI/TEST/keibabook/venv/bin/python` を選択

