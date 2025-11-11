# KeibaBook スクレイパープロジェクト

このリポジトリは WSL (Ubuntu 22.04) 上の `venv` を使い、Windows 側の `C:\GeminiCLI\TEST\keibabook` に配置して作業する想定の雛形です。

セットアップ（WSL の bash で実行）:

```bash
cd /mnt/c/GeminiCLI/TEST/keibabook
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Playwright を使う場合はブラウザをインストール
playwright install
```

使い方:

```bash
source venv/bin/activate
python run_scraper.py
```

出力は `data/` に JSON で保存されます。

注意:
- KeibaBook の利用規約と robots.txt を必ず確認してください。
- 実際にアクセスする際はレート制御を行ってください（例: 10分以上間隔）。
