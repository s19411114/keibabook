# WSL軽量環境セットアップガイド

## WSL環境でのクラッシュ・パフォーマンス問題の解決

### 1. WSLメモリ制限設定
`C:\Users\<ユーザー名>\.wslconfig` に以下をコピー：
```ini
[wsl2]
memory=4GB
processors=2
swap=2GB
pageReporting=false
nestedVirtualization=false
```

### 2. 推奨VS Code設定
- **venv自動アクティベート**: 無効化済み
- **ファイル監視除外**: data/, logs/, __pycache__/ など大容量フォルダを除外
- **Python解析**: 軽量モード（openFilesOnlyなど）
- **不要な拡張機能**: Docker, Jupyter等を除外推奨

### 3. 軽量使用方法
```bash
# WSL内で直接作業（推奨）
cd /mnt/c/GeminiCLI/TEST/keibabook
python scripts/run_single_race.py --help

# VS Codeで開く場合
code . # ターミナルからWSL内で開く
```

### 4. トラブルシューティング
**症状**: VS Codeがクラッシュ・フリーズ
**解決策**: 
1. WSL再起動: `wsl --shutdown`
2. VS Codeキャッシュクリア
3. 拡張機能を最小限に絞る

**症状**: venvが勝手にアクティベート
**解決策**: 設定済み（.vscode/settings.json参照）