# WSL軽量環境セットアップガイド（統合版）

## 🎯 目的
WSL環境でkeibabook開発時の問題を解決：
- ✅ venv自動アクティベート防止
- ✅ VS Codeクラッシュ・フリーズ防止  
- ✅ パフォーマンス最適化
- ✅ **WSLネイティブ環境移行済み**: `/home/hiro/projects/keibabook`

---

## 📋 完了済み設定（自動適用）

### VS Code設定（.vscode/settings.json）
- **venv完全無効化**: 全てのPython環境自動検出OFF
- **ファイル監視最適化**: data/, logs/, __pycache__/ など重いフォルダ除外
- **メモリ使用量削減**: Python解析・インデックス機能制限
- **カスタムbash起動**: venv強制無効化スクリプト自動実行

### 拡張機能最適化（.vscode/extensions.json）
- **推奨**: WSL, Python, Pylanceのみ
- **除外**: Docker, Jupyter, フォーマッター等

---

## 🔧 手動設定（必要に応じて）

### 1. WSL2メモリ制限（推奨）
`C:\Users\<ユーザー名>\.wslconfig` に以下をコピー：
```ini
[wsl2]
memory=4GB
processors=2
swap=2GB
pageReporting=false
nestedVirtualization=false
localhostForwarding=true

[experimental]
sparseVhd=true
autoMemoryReclaim=gradual
```
**適用方法**: WSLを再起動 `wsl --shutdown`

---

## 🚀 使用方法

### 基本ワークフロー（WSLネイティブ環境）
```bash
# 1. WSLネイティブディレクトリに移動
cd /home/hiro/projects/keibabook

# 2. VS Code起動（WSL内から）
code .

# 3. ターミナル起動時の表示確認
# "🚫 Virtual environments disabled" メッセージが表示されればOK

# 4. 必要時のvenv手動アクティベート
source /path/to/venv/bin/activate
```

### スクレイピング・UI実行例
```bash
# Streamlit UI起動（推奨）
python -m streamlit run app.py
# ブラウザ: http://localhost:8501

# 単発スクレイピング実行
python scripts/run_single_race.py --venue 浦和 --race 9 --skip-debug-files

# 高速モード
python scripts/cli_prepare_now.py --venue 浦和 --fast --rate 0.5
```

---

## 🔍 トラブルシューティング

### 問題: まだvenvが自動アクティベート
**解決策**:
1. VS Code完全再起動
2. WSL再起動: `wsl --shutdown`  
3. 新ターミナル起動でメッセージ確認

### 問題: VS Codeクラッシュ・フリーズ
**解決策**:
1. `.wslconfig`適用でメモリ制限
2. 不要な拡張機能無効化
3. ファイル監視除外確認

### 問題: パフォーマンス低下
**解決策**:
1. `--skip-debug-files`フラグ使用
2. `--rate 0.5`で高速化
3. 大容量フォルダ（data/, logs/）のクリーンアップ

---

## 📊 設定効果

| 項目 | 設定前 | 設定後 |
|------|--------|--------|
| venv自動開始 | 毎回発生 | 完全無効 |
| ファイル監視 | 全ファイル | 重要ファイルのみ |
| Python解析 | フル機能 | 軽量モード |
| メモリ使用量 | 無制限 | 4GB制限推奨 |
| スクレイピング速度 | 1-3秒/fetch | 0.5-1秒/fetch |

---

## 💡 追加の最適化

### 開発時の推奨フラグ
```bash
# デバッグファイル削減
--skip-debug-files

# レート制限高速化  
--rate 0.5

# 高速モード
--fast

# パフォーマンス計測
--perf
```

### 環境変数の手動設定（必要時）
```bash
export VIRTUAL_ENV=""
export PYTHONPATH=""
export CONDA_AUTO_ACTIVATE_BASE=false
```

---

## 🔄 設定ファイル詳細

### 主要設定項目（.vscode/settings.json）
- `python-envs.defaultEnvManager: "none"` - 環境マネージャー無効化
- `python.terminal.activateEnvironment: false` - ターミナルvenv無効化
- `terminal.integrated.inheritEnv: false` - 環境変数継承無効化
- `python.analysis.indexing: false` - インデックス機能無効化

### bash設定（.vscode/bash_profile_override）
- VIRTUAL_ENV変数のクリア
- conda/mamba/pyenvエイリアス無効化
- プロンプト正規化