# 引継ぎ資料 - Claude Haiku / 次のエージェント向け

## 📋 現在の状況

### ✅ 修正完了したバグ
1. **scrape()メソッドの構造バグ** (本日修正)
   - 問題: 外部からpage/contextを渡すと処理が実行されなかった
   - 原因: try-finallyブロックが`if created_browser`の内側にあった
   - 修正: `src/scrapers/keibabook.py`のscrape()メソッドの構造を修正
   - コミット: `8ea26c9`

### ✅ 動作確認済み
- 浦和記念(明日): 12頭のデータを約30秒で取得成功
- テスト: 全10件パス
- ファイル出力: `data/202511261811/20251126_urawa11R_*.json`

---

## 📌 ユーザーの要望（未対応）

### 1. スケジュール取得先の変更
**現状:**
- 複数のフェッチャーが存在: `JRAScheduleFetcher`, `NARScheduleFetcher`, `NetkeibaCalendarFetcher`, `KeibaTodayFetcher`
- netkeiba.com主体で取得中

**ユーザー要望:**
- 公式サイトの方がシンプルなので取得先を変更したい

**公式サイトURL:**
| タイプ | URL | 用途 |
|--------|-----|------|
| 地方カレンダー | https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop | 月間日程 |
| 地方今日 | https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/TodayRaceInfoTop | 本日レース時刻表 |
| 競馬ブック日程 | https://s.keibabook.co.jp/chihou/nittei/top | 構造複雑かも |
| JRAカレンダー | https://jra.jp/keiba/calendar/ | JRA月間 |
| JRA時間表 | https://jra.jp/keiba/calendar2025/2025/11/1124.html | 特定日の時刻表 |

**keiba.go.jpの構造（本日確認済み）:**
```
### 本日のレース
| 会場 | 1R | 2R | 3R | ... | 12R |
|------|-----|-----|-----|-----|------|
| 浦和 | 12:20 | 12:50 | 13:20 | ... | 18:20 特別 |
```
HTMLがシンプルなテーブル形式で、パースしやすい。

**作業内容:**
- `src/scrapers/keiba_today.py`のパース処理を強化（現在は汎用パース、テーブル直接パースに変更推奨）
- または新規フェッチャー作成

### 2. スケジュールデータのDB格納
**現状:**
- `CSVDBManager`は存在するがスケジュールは格納していない
- `data/db/`にCSVファイルで管理

**作業内容:**
- `CSVDBManager`にスケジュールテーブル追加
- または別途JSON/SQLiteで管理

### 3. UI（Streamlit）の問題
**ユーザー質問:** 「UIについても重大な問題あったら教えてほしい」

**確認済み問題:**
1. **asyncio.run()の使用**: `app.py`内で`asyncio.run(scraper.scrape())`を直接呼んでいる（Streamlitの再実行でイベントループ問題の可能性）
2. **importlib.reload()の多用**: モジュールのリロードが多い（パフォーマンス影響）
3. **ターミナルのPython REPLモード**: 開発中にPython REPLがアクティブになりシェルコマンドが実行できなくなる問題が頻発

**潜在的問題:**
- 大規模データ取得時のタイムアウト
- 複数会場同時取得時の問題

---

## 📁 重要ファイル一覧

### コア
| ファイル | 説明 |
|----------|------|
| `src/scrapers/keibabook.py` | メインスクレイパー（修正済み） |
| `src/scrapers/keiba_today.py` | keiba.go.jpフェッチャー |
| `src/scrapers/jra_schedule.py` | JRAスケジュール |
| `src/scrapers/nar_schedule.py` | NARスケジュール |
| `src/utils/db_manager.py` | CSVデータベース管理 |
| `scripts/run_single_race.py` | CLI単一レース取得 |

### UI
| ファイル | 説明 |
|----------|------|
| `app.py` | Streamlit GUI（1131行） |

### 設定
| ファイル | 説明 |
|----------|------|
| `config/settings.yml` | 設定ファイル |
| `cookies.json` | ログインCookie |

---

## 🔧 動作確認コマンド

### 単一レース取得（CLI）
```powershell
# 浦和11R（浦和記念）
python scripts/run_single_race.py --venue 浦和 --race 11 --shutuba-url "https://s.keibabook.co.jp/chihou/syutuba/2025111302111126" --skip-dup --perf

# 過去レースID指定
python scripts/run_single_race.py --venue 福島 --race 2 --race-id 202503060201 --skip-dup --perf
```

### テスト
```powershell
python -m pytest tests/test_scraper.py -v
```

### Streamlit起動
```powershell
streamlit run app.py
```

---

## ⚠️ 注意事項

1. **今日のレース**: 今日（2025/11/26水）は浦和・水沢・名古屋・園田で開催中
2. **Cookie**: `cookies.json`でログイン状態を維持（有効期限切れに注意）
3. **レート制限**: 1-2秒間隔、429エラー時は最大30秒バックオフ
4. **地方競馬 (NAR)**: `race_type='nar'`でchihouベースURLを使用
5. **Python REPL**: ターミナルがPython REPLになっていたら`exit()`で終了

---

## 📊 パフォーマンス基準

| 処理 | 目安時間 |
|------|----------|
| 単一レース（地方、12頭、コメント取得） | 約30秒 |
| 単一レース（中央、16頭、調教など全部） | 約60秒 |
| ページ取得 | 100-500ms/ページ |

---

## 🎯 推奨作業順序

1. **keiba.go.jp からの本日レース取得強化** (優先度: 高)
   - `src/scrapers/keiba_today.py`のテーブルパース改善
   - HTMLテーブルからレース番号と時刻を抽出

2. **スケジュールDB格納** (優先度: 中)
   - `CSVDBManager`にスケジュールテーブル追加

3. **UIの安定性改善** (優先度: 低)
   - asyncio.run()をより安全なパターンに変更

---

## 📝 最近のコミット

```
8ea26c9 fix: scrape() method bug - now works with external page/context
b97a68c feat(cli): add --race-id and --shutuba-url for explicit test runs
f33478a perf: set rate limiter to 1-2s range per request
edfa439 perf: fix performance issues - reduce 429 backoff, rate limit, and Docker optimization
```

---

作成日: 2025-11-26 01:20
作成者: Claude Opus 4.5
