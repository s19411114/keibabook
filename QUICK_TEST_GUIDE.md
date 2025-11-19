# 大井競馬夜レース クイックテストガイド

## 今日のテスト手順

### 1. 設定ファイルの準備

`config/settings.yml` を編集：

```yaml
race_type: "nar"  # 地方競馬
race_id: [大井競馬のレースID]
race_key: "oai_race_[日付]_[レース番号]"
shutuba_url: "https://s.keibabook.co.jp/chihou/syutuba/[race_id]"
seiseki_url: "https://s.keibabook.co.jp/chihou/seiseki/[race_id]"
```

### 2. スクレイピング実行

#### Streamlit GUI（推奨）
```bash
streamlit run app.py
```

1. サイドバーで「地方競馬 (NAR)」を選択
2. レースIDとURLを入力
3. 「🚀 スクレイピング開始」をクリック

#### CLI版
```bash
python run_scraper.py
```

### 3. データ確認

1. 「📊 データ確認」タブで取得したデータを確認
2. 馬柱、血統、ポイント情報、個別馬コメントが取得できているか確認

### 4. レコメンド機能のテスト

1. 「🎯 レコメンド」タブを開く
2. 「🔍 過小評価馬」: 前走好走なのに高オッズの馬を検出
3. 「💎 穴馬発見」: 穴馬候補を検出
4. 「📊 順位付け」: 総合スコアで順位付け

## 確認ポイント

### 取得データ
- [ ] 出馬表データ
- [ ] 血統データ
- [ ] 馬柱（過去3走）
- [ ] ポイント情報（地方競馬の場合）
- [ ] 個別馬コメント（地方競馬の場合）

### レコメンド機能
- [ ] 過小評価馬検出が動作する
- [ ] 穴馬発見が動作する
- [ ] 順位付けが動作する

## トラブルシューティング

### ポイント情報が取得できない
- `debug_point.html` を確認
- HTML構造に合わせて `src/scrapers/local_racing_parser.py` のセレクタを調整

### 個別馬コメントが取得できない
- 各馬の詳細ページのHTMLを確認
- `src/scrapers/local_racing_parser.py` の `parse_horse_comment()` のセレクタを調整

### URLが正しくない
- 実際の地方競馬のURL構造を確認
- `src/scrapers/keibabook.py` のURL生成部分を調整

## 今後の改善

- 実際のデータを見ながら、数式やルールを調整
- 効果のないルールは撤収
- 新しいルールを追加

