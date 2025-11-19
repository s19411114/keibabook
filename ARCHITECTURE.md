# アーキテクチャ設計

## 設計方針

**柔軟な構造**: 後からいつでも機能追加できる設計

## モジュール構成

### 1. スクレイパー層 (`src/scrapers/`)
- `keibabook.py`: メインスクレイパー（出馬表、調教、血統、コメント）
- `result_parser.py`: 結果ページパーサー
- `odds_fetcher.py`: オッズ取得（南関東競馬公式サイト連携）

### 2. データ管理層 (`src/utils/`)
- `db_manager.py`: CSVデータベース管理（重複チェック、差分取得）
- `odds_db.py`: オッズデータベース管理（オッズ履歴、分析）
- `rate_limiter.py`: レート制御（サイト負担軽減）
- `config.py`: 設定読み込み
- `logger.py`: ログ機能
- `recommender.py`: レコメンド機能

### 3. モデル層 (`src/models/`)
- `race.py`: データモデル（将来の拡張用）

### 4. アプリケーション層
- `app.py`: Streamlit GUI
- `run_scraper.py`: CLI版

## 機能追加の方法

### 新しいスクレイパーの追加

1. `src/scrapers/` に新しいファイルを作成
2. 既存のパーサーを参考に実装
3. `keibabook.py` から呼び出し

例:
```python
# src/scrapers/new_scraper.py
class NewScraper:
    def parse(self, html_content):
        # パース処理
        pass

# src/scrapers/keibabook.py
from src.scrapers.new_scraper import NewScraper
```

### 新しいデータ管理機能の追加

1. `src/utils/` に新しいファイルを作成
2. 既存のDBマネージャーを参考に実装

例:
```python
# src/utils/new_db.py
class NewDBManager:
    def save_data(self, data):
        # データ保存処理
        pass
```

### 新しい分析機能の追加

1. `src/utils/` に新しいファイルを作成
2. 既存のレコメンダーを参考に実装

例:
```python
# src/utils/new_analyzer.py
class NewAnalyzer:
    def analyze(self, data):
        # 分析処理
        pass
```

## レート制御の仕組み

### 自動レート制御

- **アクセスが少ない時間帯**: 3秒待機
- **通常時間帯**: 10秒待機
- **ランダム要素**: ±50%のばらつき

### 使用例

```python
from src.utils.rate_limiter import RateLimiter

rate_limiter = RateLimiter()
await rate_limiter.wait()  # 自動で時間帯を考慮
```

## データフロー

```
1. スクレイパー → データ取得
2. レート制御 → サイト負担軽減
3. データ管理 → CSV/JSON保存
4. 分析機能 → データ分析
5. GUI/CLI → 結果表示
```

## 拡張ポイント

### 1. 新しいデータソースの追加
- `src/scrapers/` に新しいパーサーを追加
- `keibabook.py` の `scrape()` メソッドに統合

### 2. 新しい分析機能の追加
- `src/utils/` に新しいアナライザーを追加
- `app.py` のレコメンドタブに統合

### 3. 新しいデータベースの追加
- `src/utils/` に新しいDBマネージャーを追加
- 既存のDBマネージャーと同様に使用

## ベストプラクティス

1. **レート制御**: 必ず `RateLimiter` を使用
2. **エラーハンドリング**: すべての外部アクセスで try-except
3. **ログ出力**: 重要な処理でログを出力
4. **重複チェック**: DBマネージャーを使用して重複を避ける
5. **柔軟な設計**: 後から機能追加しやすい構造を維持

