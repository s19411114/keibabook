Category: Reference
Status: Active

# データソース一覧

⚠️ **重要: このファイルの内容を削除しないこと**

このファイルには、競馬データ取得に関する重要な参考URLと出典情報が記録されています。

## JRA（中央競馬）

### 公式カレンダー
- **URL**: https://www.jra.go.jp/keiba/calendar/
- **用途**: 月間開催スケジュール取得
- **実装**: `src/scrapers/jra_schedule.py`
- **形式**: HTML（年月指定でカレンダー表示）

### オッズ情報
- **URL**: https://www.jra.go.jp/JRADB/accessO.html
- **用途**: リアルタイムオッズ取得（参考）
- **実装**: `src/scrapers/jra_odds.py`

## 地方競馬

### keiba.go.jp - 本日のレース
- **URL**: https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/TodayRaceInfoTop
- **用途**: 本日開催中のレース時刻表
- **実装**: `src/scrapers/keiba_today.py`
- **特徴**: リアルタイム更新、全場の今日の情報

### keiba.go.jp - 月間開催予定
- **URL**: https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop
- **用途**: 地方競馬の月間日程
- **実装**: `src/scrapers/keiba_schedule.py`
- **特徴**: 月単位の開催予定表

### NAR Netkeiba
- **URL**: https://nar.netkeiba.com/top/
- **用途**: 地方競馬スケジュール
- **実装**: `src/scrapers/nar_schedule.py`

### 南関東競馬（参考）
## Netkeiba

> **移管メモ (2025-12-08)**: 以下の重めの収集・解析処理は keiba-ai へ移管済み、または移管予定です。keibabook に残すのは per-race JSON 抽出や軽量なスケジューリングのみです。

- Netkeiba: `src/scrapers/netkeiba_result.py` (移管済 -> migration/to_keiba_ai/src/scrapers/netkeiba_result.py)
- Netkeiba DB: `src/scrapers/netkeiba_db_scraper.py` (移管済 -> migration/to_keiba_ai/src/scrapers/netkeiba_db_scraper.py)
- Batch pedigree: `run_pedigree.py`, `run_pedigree_safe.py`, `pedigree_queue*.json`, `pedigree_store/` (移管済/候補)
- Track bias: `src/utils/track_bias.py` (移管済 -> migration/to_keiba_ai/src/utils/track_bias.py)

> 既存の UI/軽量スクリプトは引き続き keibabook で維持します。移行に伴う呼び出し側の修正や `keiba_ai_adapter` の導入は別途行ってください。
- **用途**: 中央・地方全体のカレンダー
- **実装**: `src/scrapers/netkeiba_calendar.py`
- **特徴**: 視覚的なカレンダー表示

### レース結果・トラックバイアス分析
- **URL**: https://race.netkeiba.com/race/result.html?race_id={race_id}
- **用途**: レース結果取得とトラックバイアス分析（着順、通過順位、上がり3F、枠番などから脚質・内外有利を判定）
- **実装**: `src/scrapers/netkeiba_result.py`, `src/utils/track_bias.py`
- **特徴**: 過去レース結果をアーカイブして傾向分析に活用
- **例**: `race_id=202505050812` (2025年5月5日 東京8R 12レース)

## データ取得戦略

### 優先順位（JRA）
1. **Netkeiba** カレンダー（負荷分散のため）
2. **JRA** 公式カレンダー（フォールバック）
3. **keiba.go.jp** Today（最終手段）

### 優先順位（地方競馬）
1. **NAR**/Netkeiba スケジュール
2. **keiba.go.jp** 月間予定（フォールバック）

詳細は `docs/MULTI_SOURCE_STRATEGY.md` を参照。

## メンテナンス履歴

- 2025-11-30: データソース一覧を独立ファイルとして作成
- 削除禁止の注意書きを追加