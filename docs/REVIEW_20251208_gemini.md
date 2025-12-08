---
Title: Code Review - KeibaBook Application
Author: Gemini Agent
Date: 2025-12-08
Category: review
Status: open
Tags: review, design, bugs, improvement
---

# コードレビュー: KeibaBook スクレイパー

## 概要

このレビューは2025年12月8日時点でのKeibaBookアプリケーション全体を対象とした包括的なコードレビューです。
機能分離の効果、設計上の課題、バグ、改善提案をまとめています。

---

## 1. アーキテクチャ評価

### 1.1 現在の構造

```
src/
├── scrapers/    # 20ファイル (keibabook.py: 1406行, httpx_scraper.py: 27KB等)
├── utils/       # 20ファイル (db_manager.py: 535行, exporter.py: 21KB等)
├── ui/          # 3ファイル (track_bias_tab.py, training_evaluation_tab.py)
└── models/      # 2ファイル (race.py)
```

### 1.2 機能分離の評価

**成功している点 ✅:**
- `src/ui/` への UI コンポーネント分離（`track_bias_tab.py`, `training_evaluation_tab.py`）
- `comment_aggregator.py` への個別コメント集約ロジックの分離
- `training_converter.py` への調教タイム変換ロジック分離
**課題・改善余地 ⚠️:**
- `keibabook.py` は依然1406行と大きい。`scrape()` メソッド内のネストが深い
- `app.py` は786行。タブごとの分離が `src/ui/` に部分的なため一貫性がない
- スクレイピングワークフローの各フェーズ（login, fetch, parse, merge）がまだ1メソッド内に集中

### 1.3 分離の効果

| 指標 | 期待効果 | 現状評価 |
|------|----------|----------|
| 保守性 | 高い | 中～高 (パーサー分離は○、メイン処理は△) |
| テスト容易性 | 高い | 中 (36テストファイル存在するが、統合テスト中心) |
| 可読性 | 高い | 中 (ドキュメントコメントは充実、ただしネスト深い) |
| 拡張性 | 高い | 高 (新規パーサー追加は容易) |

---

## 2. バグ報告

- **severity**: medium
- **status**: TODO
- **files**: 
```python
# 例: src/scrapers/keibabook.py:311-313
except Exception:
    # 判定に失敗してもフェールセーフとして再取得を許す
    return False
```

**推奨修正**:
```python
except Exception as e:
    logger.debug(f"重複チェック判定エラー（フェールセーフで再取得許可）: {e}")
    return False
```

### BUG-002: 未使用の base_url 再計算

- **severity**: low
- **status**: TODO
- **file**: `src/scrapers/keibabook.py` (line 1131, 1169)

```python
base_url = '/'.join(self.settings['shutuba_url'].split('/')[:4])  # 2回計算
```

**問題点**: 同じ計算が複数回実行されている。

### BUG-003: ログイン認証の信頼性問題 (2025-12-08追加)

- **status**: IMPROVED

- **severity**: high
- **status**: TODO
- **files**:
  - `src/utils/keibabook_auth.py`
  - `src/utils/login.py`
  - `config/settings.yml`

**根本原因**:
1. **馬の数による認証確認の脆弱性**: `horse_count >= 6` で判定しているが、少頭数レースや開催日外では誤検出
2. **CSSセレクタの不一致**: `table.syutuba` を使用しているが、実際のHTMLは `table.syutuba_sp`
3. **認証情報の未設定**: `settings.yml` の `login_id/login_password` が空のため、Cookie失効時に再ログイン不可
4. **エラーログの不足**: 失敗時の原因特定が困難

**影響**:
- 未ログイン状態では3頭分のデータしか取得できない
- 血統・調教データが不完全になる

**推奨修正**:
1. 環境変数 `LOGIN_ID`, `LOGIN_PASSWORD` を設定 (KeibaBookAuth で環境変数からのフォールバックを実装しました)
2. CSSセレクタに `table.syutuba_sp tbody tr` を追加
3. 認証確認方法をログアウトリンク存在確認等に変更検討

**実施**: `verify_login_by_horse_count` にログアウトリンク/『ログアウト』文言チェックを追加して判定精度を向上

**詳細レポート**: [ログイン問題バグ調査レポート](file:///home/u/.gemini/antigravity/brain/4265f8df-30be-4a64-943e-dc9cd47bdc9b/implementation_plan.md)

---

## 3. 設計上の課題

### DESIGN-001: scrape() メソッドの複雑性

- **priority**: P2
- **status**: TODO

**現状**: `scrape()` メソッドは約400行（1000-1400行目）で、以下のフェーズが1メソッド内に存在:
1. ブラウザ/コンテキスト管理
2. ログイン処理
3. 重複チェック
4. 出馬表取得・パース
5. 調教データ取得
6. 血統データ取得
7. 厩舎/前走コメント取得
8. 結果ページ取得
9. CPU予想マージ
10. コメント集約
11. 特集ページ取得

**推奨リファクタ**:
```python
async def scrape(self, ...):
    browser_ctx = await self._ensure_browser(context, page)
    try:
        await self._ensure_login(browser_ctx)
        if await self._should_skip_race(): return {}
        
        race_data = await self._fetch_and_parse_shutuba(browser_ctx)
        race_data = await self._enrich_with_training(race_data, browser_ctx)
        race_data = await self._enrich_with_pedigree(race_data, browser_ctx)
        race_data = await self._enrich_with_comments(race_data, browser_ctx)
        race_data = await self._enrich_with_special_pages(race_data, browser_ctx)
        
        return race_data
    finally:
        await self._cleanup_browser(browser_ctx)
```

### DESIGN-002: app.py の一貫性のないタブ分離

- **priority**: P3
- **status**: TODO

**現状**:
- `tab3` (トラックバイアス) → `src/ui/track_bias_tab.py` ✅
- `tab_training` (調教) → `src/ui/training_evaluation_tab.py` ✅
- `tab1`, `tab2`, `tab4`, `tab5` → `app.py` 内にインライン ❌

**推奨**: 全タブを `src/ui/` に分離して一貫性を確保

---

## 4. 改善提案

### IMPROVE-001: 型ヒントの追加

- **priority**: P3
- **impact**: 保守性向上、IDE補完、静的解析
- **対象**: `keibabook.py`, `db_manager.py`, `app.py`

### IMPROVE-002: Pydantic モデルの導入

- **priority**: P3
- **impact**: データバリデーション、シリアライズ/デシリアライズの一貫性

```python
# 現状: Dict[str, Any] を多用
race_data: Dict[str, Any] = {}

# 推奨: Pydanticモデル
class HorseData(BaseModel):
    horse_num: str
    horse_name: str
    prediction_mark: str = ""
    odds: Optional[float] = None
    # ...
```

### IMPROVE-003: 構造化ログの導入

- **priority**: P3
- **impact**: ログ分析、監視、デバッグ効率化

```python
# 推奨: 構造化ログ
logger.info("データ取得完了", extra={
    "race_id": race_id,
    "horse_count": len(horses),
    "fetch_time_ms": elapsed
})
```

### IMPROVE-004: .bak ファイルのクリーンアップ

- **priority**: P1
- **status**: TODO

**発見されたバックアップファイル**:
- `.venv/bin/activate.bak`
- `docs/archived/archived-20251207T145738Z-exporter.py.bak`
- `docs/archived/archived-20251207T145738Z-keibabook.py.bak`
- `docs/archived/archived-20251207T145738Z-result_parser.py.bak`

**推奨**: `.gitignore` に `*.bak` を追加、既存ファイルは削除または明示的にアーカイブ

---

## 5. テスト状況

### 5.1 テストカバレッジ

- **テストファイル数**: 36
- **主要テスト**:
  - `test_scraper.py` (28KB) - 統合テスト
  - `test_training_offline.py` (15KB) - 調教パース
  - `test_training_conversion.py` (12KB) - タイム変換
  - `test_db_integration.py` - DB操作

### 5.2 テスト追加推奨

| テスト対象 | 優先度 | 理由 |
|-----------|--------|------|
| レート制限 | P2 | 現在テストなし |
| エラーリトライ | P2 | 失敗パスのカバレッジ |
| コメント集約 | P3 | 新規分離したモジュール |

---

## 6. 次のアクション推奨

### 即座に対応（P1）
1. `.bak` ファイルのクリーンアップと `.gitignore` 更新
2. bare except の修正

### 計画的に対応（P2）
1. `scrape()` メソッドのリファクタリング
2. 残りのタブを `src/ui/` に分離
3. レート制限テストの追加

### 将来的に検討（P3）
1. 型ヒントの追加
2. Pydantic モデル導入
3. 構造化ログ導入
4. CI/CD パイプラインでのlint強化

---

## 7. 関連ドキュメント

- [ISSUES_MASTER.md](file:///home/u/projects/TEST/keibabook/docs/ISSUES_MASTER.md) - タスク/バグ台帳
- [ARCHITECTURE.md](file:///home/u/projects/TEST/keibabook/ARCHITECTURE.md) - アーキテクチャ設計
- [AGENT_RULES.md](file:///home/u/projects/TEST/keibabook/AGENT_RULES.md) - エージェント向けルール

---

**レビュー完了日**: 2025-12-08
**レビュー担当**: Gemini Agent
**次回レビュー推奨**: 主要リファクタリング完了後
