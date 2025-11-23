# オッズ取得機能ガイド

## 概要

南関東競馬公式サイトからオッズを5分置きに取得し、データベースに記録する機能です。
オッズの変化を分析して、八百長検出や予想機能に活用できます。

## 機能

### 1. オッズ取得 (`src/scrapers/odds_fetcher.py`)
- 南関東競馬公式サイトからオッズを取得
- レート制御（ランダム待機、アクセス少ない時間帯の考慮）
- 5分置きの定期取得に対応

### 2. オッズデータベース (`src/utils/odds_db.py`)
- オッズ履歴の保存
- オッズの動きを分析
- 不審な動きの検出（八百長検出のヒント）

## 使い方

### 基本的な使い方

```python
from src.scrapers.odds_fetcher import OddsFetcher
from src.utils.odds_db import OddsDBManager
from playwright.async_api import async_playwright

settings = {'race_id': '202503060201', 'race_type': 'jra'}
odds_fetcher = OddsFetcher(settings)
odds_db = OddsDBManager()

async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    
    # オッズを取得
    odds_data = await odds_fetcher.fetch_odds(page)
    
    # データベースに保存
    odds_db.save_odds(odds_data)
```

### 定期取得（5分置き）

```python
import asyncio
import schedule
import time

async def fetch_odds_periodically():
    settings = load_settings()
    odds_fetcher = OddsFetcher(settings)
    odds_db = OddsDBManager()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        while True:
            odds_data = await odds_fetcher.fetch_odds(page)
            if odds_data:
                odds_db.save_odds(odds_data)
            
            # 5分待機
            await asyncio.sleep(300)

# 実行
asyncio.run(fetch_odds_periodically())
```

## オッズ分析

### オッズ履歴の取得

```python
odds_db = OddsDBManager()

# 特定レースの全頭のオッズ履歴
history = odds_db.get_odds_history('202503060201')

# 特定の馬のオッズ履歴
horse_history = odds_db.get_odds_history('202503060201', horse_num='1')
```

### オッズの動きを分析

```python
# オッズの変化を分析
analysis = odds_db.analyze_odds_movement('202503060201')

# 結果例:
# {
#   '1': {
#     'first_odds': 10.5,
#     'last_odds': 8.2,
#     'max_odds': 12.0,
#     'min_odds': 8.2,
#     'change_rate': -21.9,  # 21.9%下落
#     'data_points': 10
#   }
# }
```

### 不審な動きを検出

```python
# 急激なオッズの変化を検出（八百長検出のヒント）
suspicious = odds_db.detect_suspicious_movement('202503060201', threshold=50.0)

# 結果例:
# [
#   {
#     'horse_num': '1',
#     'change_rate': -55.2,
#     'first_odds': 100.0,
#     'last_odds': 45.0,
#     'reason': 'オッズが55.2%急落'
#   }
# ]
```

## レート制御

### 自動レート制御

- **アクセスが少ない時間帯（0-6時、23-24時）**: 3秒待機
- **通常時間帯**: 10秒待機
- **ランダム要素**: ±50%のばらつきを追加

### 手動レート制御

```python
from src.utils.rate_limiter import RateLimiter

rate_limiter = RateLimiter(base_delay=5)  # 5秒待機
await rate_limiter.wait(randomize=True)  # ランダム要素あり
```

## データベース構造

### オッズ履歴テーブル (`odds_history.csv`)

| カラム | 説明 |
|--------|------|
| race_id | レースID |
| horse_num | 馬番 |
| win_odds | 単勝オッズ |
| place_odds | 複勝オッズ |
| popularity | 人気 |
| fetched_at | 取得日時 |
| timestamp | タイムスタンプ |

## 今後の拡張

- [ ] オッズ変化の可視化（グラフ表示）
- [ ] 八百長検出アルゴリズムの改善
- [ ] 予想機能との連携
- [ ] 配当金との相関分析

## 注意事項

- 南関東競馬公式サイトのURLは実際のURLに置き換えが必要です
- HTML構造に応じてパーサーを調整してください
- レート制御を適切に設定して、サイト負担を軽減してください

