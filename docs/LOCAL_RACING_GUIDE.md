# 地方競馬（NAR）対応ガイド

## 概要

現在の実装は中央競馬（JRA）用ですが、地方競馬（NAR）にも対応できる設計になっています。

## 設定方法

### 1. 設定ファイルで競馬種別を指定

`config/settings.yml` で `race_type` を設定：

```yaml
# 中央競馬の場合
race_type: "jra"
shutuba_url: "https://s.keibabook.co.jp/cyuou/syutuba/202503060201"

# 地方競馬の場合
race_type: "nar"
shutuba_url: "https://s.keibabook.co.jp/chihou/syutuba/202503060201"
```

### 2. Streamlit GUIで選択

Streamlit GUIのサイドバーで「中央競馬 (JRA)」または「地方競馬 (NAR)」を選択できます。

## 地方競馬対応の注意点

### URL構造の違い

中央競馬と地方競馬でURL構造が異なる可能性があります：

- **中央競馬**: `https://s.keibabook.co.jp/cyuou/...`
- **地方競馬**: `https://s.keibabook.co.jp/chihou/...`（推測）

実際のURL構造を確認して、必要に応じて `src/scrapers/keibabook.py` のURL生成部分を調整してください。

### HTML構造の違い

地方競馬のHTML構造が中央競馬と異なる場合、以下のセレクタを調整する必要があります：

1. **出馬表ページ** (`_parse_race_data`)
   - `.racemei`, `.racetitle_sub`, `.syutuba_sp` など

2. **調教ページ** (`_parse_training_data`)
   - `.default.cyokyo`, `.cyokyodata` など

3. **血統ページ** (`_parse_pedigree_data`)
   - `.PedigreeTable` など

4. **コメントページ** (`_parse_stable_comment_data`, `_parse_previous_race_comment_data`)
   - `.StableCommentTable`, `.PreviousRaceCommentTable` など

5. **馬柱** (`_parse_horse_table_data`)
   - 過去成績テーブルのセレクタ

### 調整方法

1. **実際のHTMLを確認**
   - 地方競馬のページを開いて、`debug_page.html` を確認
   - ブラウザの開発者ツールでHTML構造を確認

2. **セレクタを追加**
   - 既存のセレクタに加えて、地方競馬用のセレクタを追加
   - 例: `.syutuba_sp, .syutuba_nar` のように複数のセレクタを指定

3. **条件分岐を追加**
   - `self.race_type` で分岐して、異なるパーサーを使用

## 実装例

### セレクタの追加例

```python
# 中央競馬と地方競馬の両方に対応
shutuba_table = soup.select_one(".syutuba_sp, .syutuba_nar, table.syutuba")
```

### 条件分岐の例

```python
if self.race_type == 'nar':
    # 地方競馬用の処理
    shutuba_table = soup.select_one(".syutuba_nar")
else:
    # 中央競馬用の処理
    shutuba_table = soup.select_one(".syutuba_sp")
```

## テスト方法

1. **地方競馬のレースURLを取得**
   - 実際の地方競馬の出馬表ページURLを取得

2. **設定ファイルを更新**
   - `race_type: "nar"` に設定
   - `shutuba_url` を地方競馬のURLに変更

3. **スクレイピングを実行**
   - `python run_scraper.py` または Streamlit GUIで実行

4. **デバッグHTMLを確認**
   - `debug_page.html` を確認して、HTML構造を把握

5. **セレクタを調整**
   - 必要に応じてパーサーのセレクタを調整

## 今後の拡張

- [ ] 地方競馬の実際のURL構造を確認
- [ ] HTML構造の違いを確認
- [ ] セレクタの調整
- [ ] 地方競馬専用のパーサーを作成（必要に応じて）

## 参考情報

- 中央競馬: JRA（日本中央競馬会）
- 地方競馬: NAR（地方競馬全国協会）

