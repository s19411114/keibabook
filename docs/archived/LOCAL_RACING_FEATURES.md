# 地方競馬専用機能
Status: archived

Note: This document contains features that are not currently in active use and were likely generated during a short trial period. It has been archived for historical reference and may be removed in a later cleanup step.

## 概要

地方競馬は収入源として重要であるため、専用の機能を実装しています。

## 取得する情報

### 1. ポイント情報（`point`ページ）

地方競馬のポイントページから以下の情報を取得：

- **今日大穴空けた馬たち**: 大穴を空けた馬の情報
- **激走した馬たちのヒント**: 激走した馬のヒント
- **血統からAIが予想した馬たち**: AIが血統から予想した馬
- **パワー要る馬場の馬**: 高オッズ（100倍、200倍）で掲示板や3着来た馬など
- **掲示板の馬**: 掲示板に載った馬

これらの情報は本当に当たっているため、穴馬発見の重要なヒントになります。

### 2. 個別馬のコメント

各馬の詳細ページからコメントを取得します。穴馬のヒントになる重要な情報です。

## 実装状況

### ポイントページの取得

```python
# src/scrapers/keibabook.py の _scrape_point_page() メソッド
point_data = await self._scrape_point_page(page, base_url)
```

取得されるデータ構造：
```json
{
  "point_info": {
    "big_upset_horses": [
      {
        "horse_num": "1",
        "horse_name": "馬名",
        "reason": "理由",
        "odds": "100.0"
      }
    ],
    "strong_run_hints": [...],
    "ai_pedigree_picks": [...],
    "power_track_horses": [...],
    "board_horses": [...]
  }
}
```

### 個別馬コメントの取得

```python
# src/scrapers/keibabook.py の _scrape_horse_comments() メソッド
await self._scrape_horse_comments(page, horses, base_url)
```

各馬のデータに `individual_comment` フィールドが追加されます。

## 対戦成績について

対戦成績は過去3年以上前のデータも含まれ、情報量が多すぎるため：

1. **現時点では取得しない**
2. **過去走結果を集めてから指数表・レーティング表を作成**
3. **こちらで作成した指数表・レーティング表で対処**

## 注意事項

### URL構造の確認

実際の地方競馬サイトのURL構造に合わせて以下を調整してください：

1. **ポイントページのURL**
   - `src/scrapers/keibabook.py` の `_scrape_point_page()` メソッド
   - 現在: `{base_url}/point/{race_id}`
   - 実際のURL構造に合わせて調整

2. **個別馬ページのURL**
   - `src/scrapers/keibabook.py` の `_scrape_horse_comments()` メソッド
   - 現在: 馬名リンクから取得
   - 実際のURL構造に合わせて調整

### HTML構造の確認

実際のHTML構造に合わせて以下を調整してください：

1. **ポイントページのセレクタ**
   - `src/scrapers/local_racing_parser.py` の `parse_point_page()` メソッド
   - セレクタを実際のHTML構造に合わせて調整

2. **個別馬コメントのセレクタ**
   - `src/scrapers/local_racing_parser.py` の `parse_horse_comment()` メソッド
   - セレクタを実際のHTML構造に合わせて調整

## デバッグ方法

1. **ポイントページのHTMLを確認**
   - `debug_point.html` を確認
   - 実際のHTML構造を把握
   - セレクタを調整

2. **個別馬ページのHTMLを確認**
   - 各馬の詳細ページのHTMLを確認
   - コメントの位置を特定
   - セレクタを調整

## 今後の拡張

- [ ] 対戦成績の取得（過去走結果を集めてから）
- [ ] 指数表・レーティング表の作成
- [ ] ポイント情報の可視化
- [ ] 穴馬検出アルゴリズムの改善


ArchivedAt: 2025-12-06T16:05:03.013270
