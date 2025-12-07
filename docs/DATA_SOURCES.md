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
- **URL**: https://www.nankankeiba.com/odds/race/{race_id}
- **用途**: 南関東4場のオッズ（参考）
- **実装**: `src/scrapers/odds_fetcher.py`

## Netkeiba

> **Policy Update (2025-12-06)**: Netkeiba の過去データ収集（Netkeiba DB のアーカイブ、結果ページのトラックバイアス計算、batch pedigree の収集など）は keiba-ai プロジェクトに移管します。
> See: migration/to_keiba_ai/manifest.md and migration/to_keiba_ai/README.md

### カレンダー
- **URL**: https://race.netkeiba.com/top/calendar.html?rf=sidemenu
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
