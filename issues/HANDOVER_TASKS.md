# 他エージェント向け引継ぎタスク

**作成日**: 2025年11月25日  
**参照**: `issues/PERFORMANCE_ANALYSIS.md` （問題分析レポート）

---

## 🎯 概要

このドキュメントは、KeibaBook Scraperの改善タスクのうち、時間のかかる作業を他のエージェントに引き継ぐための指示書です。

---

## タスク1: Docker環境の最適化

### 目的
Docker内でのスクレイピング実行を高速化する

### 現状の問題
- `mcr.microsoft.com/playwright/focal` イメージは毎回 `pip install` が必要
- WSL2経由のボリュームマウントが遅い
- Chromiumの初回起動オーバーヘッド

### 作業内容
1. `Dockerfile` を更新して依存関係をプリインストール
2. `docker-compose.yml` にパフォーマンス最適化オプションを追加
3. テスト実行して時間を計測

### 参考コード

```dockerfile
# Dockerfile 改善案
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# 依存関係をコピーして先にインストール（キャッシュ活用）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

CMD ["bash"]
```

```yaml
# docker-compose.yml 改善案
services:
  app:
    build: .
    container_name: keibabook-dev
    volumes:
      # delegated で書き込みパフォーマンス向上
      - ${HOST_PROJECT_DIR:-.}:/app:delegated
      - /app/venv
      - /app/__pycache__
      - /app/data  # データフォルダもDockerボリュームに
    environment:
      - PYTHONUNBUFFERED=1
      - PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
    # メモリ・CPU制限の明示
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2'
```

### 成功基準
- Docker内で `run_single_race.py --venue 浦和 --race 9` が60秒以内に完了

---

## タスク2: run_pedigree.py の非同期化

### 目的
血統データ取得を並列化して高速化

### 現状の問題
- `requests` ライブラリで同期的にURLを1つずつ取得
- 数百URLの場合、数時間かかる

### 作業内容
1. `requests` を `aiohttp` に置き換え
2. `asyncio.Semaphore` で並列数を制御（サイト負荷軽減）
3. エラー処理とリトライロジックを維持

### 参考コード

```python
# run_pedigree_async.py（新規作成）
import asyncio
import aiohttp
import json
from pathlib import Path

CONCURRENCY = 3  # 同時接続数
BASE_DELAY = 1.0

async def fetch_pedigree(session, semaphore, url, store_dir):
    async with semaphore:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    # パース処理...
                    return {'url': url, 'status': 'success'}
                elif resp.status == 429:
                    await asyncio.sleep(30)
                    return {'url': url, 'status': 'retry'}
        except Exception as e:
            return {'url': url, 'status': 'error', 'error': str(e)}
        finally:
            await asyncio.sleep(BASE_DELAY)

async def main():
    pq = Path('pedigree_queue.json')
    urls = json.load(open(pq, encoding='utf-8'))
    store_dir = Path('pedigree_store')
    store_dir.mkdir(exist_ok=True)
    
    semaphore = asyncio.Semaphore(CONCURRENCY)
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_pedigree(session, semaphore, url, store_dir) for url in urls]
        results = await asyncio.gather(*tasks)
    
    success = sum(1 for r in results if r['status'] == 'success')
    print(f"Done: {success}/{len(urls)} URLs fetched")

if __name__ == '__main__':
    asyncio.run(main())
```

### 成功基準
- 100 URLs が 5分以内に処理可能
- サイトから429エラーが頻発しないこと

---

## タスク3: テストスイートの拡充

### 目的
パフォーマンス問題の再発を防ぐための自動テスト追加

### 作業内容
1. `tests/test_rate_limiter.py` を作成
2. `tests/test_scraper_performance.py` を作成
3. CI/CDでのタイムアウト検出

### 参考コード

```python
# tests/test_rate_limiter.py
import pytest
import asyncio
from src.utils.rate_limiter import RateLimiter

@pytest.mark.asyncio
async def test_rate_limiter_max_wait():
    """レート制限の待機時間が3秒を超えないことを確認"""
    limiter = RateLimiter(base_delay=3.0)
    import time
    start = time.perf_counter()
    await limiter.wait()
    elapsed = time.perf_counter() - start
    assert elapsed < 4.0, f"Wait time {elapsed}s exceeded expected maximum"

@pytest.mark.asyncio
async def test_rate_limiter_custom_delay():
    """カスタム待機時間が正しく適用されることを確認"""
    limiter = RateLimiter(base_delay=0.5)
    import time
    start = time.perf_counter()
    await limiter.wait(randomize=False)
    elapsed = time.perf_counter() - start
    assert 0.4 < elapsed < 0.7, f"Wait time {elapsed}s not within expected range"
```

```python
# tests/test_scraper_performance.py
import pytest
import asyncio
import time

@pytest.mark.asyncio
@pytest.mark.slow
async def test_single_race_scrape_under_60s():
    """1レースのスクレイピングが60秒以内に完了することを確認"""
    # モックを使用してネットワーク遅延をシミュレート
    # 実際のテストでは適宜調整
    pass
```

### 成功基準
- 全テストがパス
- CIで5分以内に全テスト完了

---

## タスク4: ログ・モニタリング改善

### 目的
長時間実行の原因を特定しやすくする

### 作業内容
1. 各フェッチの所要時間をログ出力（既存の `PERF` ログを活用）
2. 429エラー発生回数のカウント
3. 実行時間のサマリーをJSON出力

### 参考コード

```python
# src/utils/perf_logger.py（新規作成）
import time
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List

@dataclass
class FetchRecord:
    url: str
    status: int
    duration_ms: float
    is_retry: bool = False
    error: str = None

class PerfLogger:
    def __init__(self, race_key: str):
        self.race_key = race_key
        self.records: List[FetchRecord] = []
        self.start_time = time.perf_counter()
    
    def log_fetch(self, url: str, status: int, duration_ms: float, **kwargs):
        self.records.append(FetchRecord(url=url, status=status, duration_ms=duration_ms, **kwargs))
    
    def save_summary(self, output_dir: Path):
        elapsed = time.perf_counter() - self.start_time
        summary = {
            'race_key': self.race_key,
            'total_elapsed_ms': elapsed * 1000,
            'fetch_count': len(self.records),
            'error_count': sum(1 for r in self.records if r.error),
            '429_count': sum(1 for r in self.records if r.status == 429),
            'records': [asdict(r) for r in self.records]
        }
        out_file = output_dir / f'perf_{self.race_key}.json'
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        return out_file
```

### 成功基準
- 実行後に `perf_*.json` が生成される
- 429エラー回数が容易に確認できる

---

## 📋 タスク優先順位

| タスク | 優先度 | 推定時間 | 担当 |
|--------|--------|----------|------|
| タスク1: Docker最適化 | 高 | 2-3時間 | 未割当 |
| タスク2: 非同期化 | 中 | 3-4時間 | 未割当 |
| タスク3: テスト拡充 | 中 | 2-3時間 | 未割当 |
| タスク4: ログ改善 | 低 | 1-2時間 | 未割当 |

---

## 📌 注意事項

1. **サイト負荷**: 並列数を上げすぎると429エラーが増加するため、CONCURRENCY=3程度を推奨
2. **Cookie**: ログイン状態を維持するため `cookies.json` を適切に管理
3. **テスト環境**: 本番サイトへのアクセスを伴うテストは `@pytest.mark.slow` でマーク
