Category: Issue
Status: Active

# KeibaBook Scraper パフォーマンス問題分析レポート

**作成日**: 2025年11月25日  
**問題**: 1レース1分程度で終了していた作業が数十分〜数時間かかるようになった

---

## 🔴 緊急度：高（即時修正が必要）

### 1. 429 Too Many Requests バックオフが過大
**ファイル**: `src/scrapers/keibabook.py` (行76-78)

```python
wait_seconds = min(60 * (attempt + 1), 300)  # 最大300秒（5分）待機
```

**問題点**:
- 429エラー発生時、attempt 1 で60秒、attempt 2 で120秒、attempt 3 で180秒待機
- retry_count=3 の場合、最悪で 60+120+180 = **360秒（6分）** 待機
- **複数URLで429が発生すると累積で数時間になる**

**修正案**: バックオフ上限を30秒に制限
```python
wait_seconds = min(10 * (attempt + 1), 30)  # 最大30秒
```

---

### 2. コンテナ（Docker）関連の注記
Dockerによる再現は非推奨です。ホスト環境（`.venv`）での再現手順を推奨します。WSL固有の I/O 遅延や共有マウントの問題がある場合、WSL 設定（`.wslconfig`のメモリ増/スワップ増）やホスト実行での再現を推奨します。

---

### 3. ログイン確認で追加のページナビゲーション
**ファイル**: `src/scrapers/keibabook.py` (行520-527), `src/utils/login.py`

**問題点**:
- `ensure_logged_in()` が毎回新しいページを開いて閉じる
- ログイン確認だけで `wait_for_load_state("networkidle")` を使用（遅い）

**修正案**: Cookie有効期限をチェックしてログイン確認をスキップ

---

### 4. scrape() メソッド内で新ブラウザ起動
**ファイル**: `src/scrapers/keibabook.py` (行499-506)

**問題点**:
- `page=None` の場合、`scrape()`が独自にブラウザを起動
- しかし `run_single_race.py` は既にブラウザを渡しているので、`scrape()` 内の `created_browser=True` ブロックが**デッドコード**になっている
- 問題は**スクレイピングロジック全体が `try` ブロック内に入っている**こと

**修正案**: ロジックを分離してコードを整理

---

## 🟡 緊急度：中（早期対応推奨）

### 5. 各URLフェッチごとのレート制限
**ファイル**: `src/scrapers/keibabook.py`、`src/utils/rate_limiter.py`

**問題点**:
- 1レースで約6-8回のURLフェッチ（出馬表、調教、血統、厩舎コメント、前走コメント等）
- 各フェッチに1〜3秒の待機が入る → **最低18〜24秒の待機時間**
- 地方競馬（NAR）の場合、特定の馬のコメントも取得するためさらに遅い

**修正案**:
- デフォルトの `rate_limit_base` を0.5秒に短縮
- 同一ドメインへの連続アクセスは待機時間を短縮

---

### 6. デバッグファイル書き込み
**ファイル**: `src/scrapers/keibabook.py`

**問題点**:
- `--skip-debug-files` を指定しない限り、`debug_page_*.html`、`debug_fetches_*.json` 等を毎回書き込む
- Docker内のボリュームマウントへの書き込みは特に遅い

**対応状況**: `--skip-debug-files` フラグは既に実装済み

---

### 7. cli_prepare_now.py の重複 `--perf` 引数
**ファイル**: `scripts/cli_prepare_now.py` (行127-128)

```python
parser.add_argument('--perf', action='store_true', help='Enable per-step perf logs')
parser.add_argument('--perf', action='store_true', help='Enable per-step perf logs')  # 重複！
```

**修正案**: 重複行を削除

---

## 🟢 緊急度：低（中長期改善）

### 8. Playwright wait_until 設定
**ファイル**: `src/scrapers/keibabook.py` (行70)

**問題点**:
- デフォルトで `domcontentloaded` を使用しているが、サイトによっては `load` や `networkidle` が必要
- 動的コンテンツの場合、早すぎると正しいデータが取得できない

**現状**: 設定可能（`playwright_wait_until`）

---

### 9. run_pedigree.py の同期処理
**ファイル**: `run_pedigree.py`

**問題点**:
- `requests` を使った同期処理（`asyncio` 非対応）
- 大量のURL処理で時間がかかる

**修正案**: `aiohttp` + `asyncio.gather` での並列化

---

### 10. cli_minimal_odds.py のスケジュール待機
**ファイル**: `scripts/cli_minimal_odds.py` (行153-156)

```python
await asyncio.sleep(wait_seconds)  # レース発走まで待機
```

**説明**: これは意図的な動作（発走前10分/4分にオッズを取得）
**対応**: 問題なし（長時間実行は設計通り）

---

## 📋 即時修正項目チェックリスト

| # | 項目 | 優先度 | 状態 |
|---|------|--------|------|
| 1 | 429バックオフ上限を30秒に制限 | 高 | 修正予定 |
| 2 | cli_prepare_now.py の重複引数削除 | 中 | 修正予定 |
| 3 | RateLimiter デフォルト待機時間短縮 | 中 | 修正予定 |
| 4 | Docker起動コマンド改善 | 中 | ドキュメント追加 |

---

## 🛠 実行コマンド（推奨）
Docker 実行例は削除されました（非推奨）。ホスト環境での再現手順を使用してください。

```bash
cd /path/to/keibabook
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/run_single_race.py --venue 浦和 --race 9 --skip-debug-files
```
---

## 📊 期待される改善効果

| 修正項目 | 修正前 | 修正後 | 短縮時間 |
|----------|--------|--------|----------|
| 429バックオフ | 最大300秒/回 | 最大30秒/回 | -270秒/回 |
| レート制限 | 1-3秒/fetch | 0.5-1秒/fetch | -2秒/fetch |
| デバッグファイル | 毎回書き込み | スキップ可 | -1〜2秒/fetch |
| **合計（8 fetch）** | **24〜48秒** | **4〜8秒** | **-20〜40秒** |

429エラーが発生しない通常ケースでは、**1レース1分以内** に戻る見込み。

---

## 🔄 他エージェント向け引継ぎ事項

別ファイル `issues/HANDOVER_TASKS.md` を参照してください。