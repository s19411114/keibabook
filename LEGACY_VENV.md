## Legacy: 仮想環境 (venv) のセットアップと使用

このドキュメントは、Dockerを使わないでローカルの仮想環境（venv）を使う場合の手順と注意点をまとめています。
通常は Docker を推奨しますが、必要に応じて参照してください。

### 初回セットアップ
```bash
cd /mnt/c/GeminiCLI/TEST/keibabook
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

### 作業開始(毎回)
```bash
cd /mnt/c/GeminiCLI/TEST/keibabook
source venv/bin/activate
```

### スクレイピング等の実行
```bash
python run_scraper.py
streamlit run app.py
pytest tests/
```

### 注意点
- Docker を使用する場合、`venv`は不要です。両方を同時に使うと依存が混在する可能性があるため注意してください。
- 依存関係は `requirements.txt` にまとめ、どちらか一方のプロセスでのみ管理してください。

### トラブルシューティング
- ModuleNotFoundErrorが出る場合は `pip install -r requirements.txt` を実行してください。
- Playwright のブラウザがない場合は `playwright install chromium` を実行してください。

---

LEGACY_VENV.md はバックアップ目的であり、通常の作業は Docker を使用してください。