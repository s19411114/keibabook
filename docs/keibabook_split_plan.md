---
Title: Implementation Plan: KeibaBook Scraper Split
Author: Automated Assistant
Date: 2025-12-07
Status: draft
Tags: refactor, scrapers, split
---

# 実装計画: KeibaBookScraper 分割

## 目的
KeibaBook の `keibabook.py` は肥大化しており可読性・テスト性が低下しているため、責務を分割し保守性を向上します。

## 成果物
- `src/scrapers/fetcher.py` - ページ取得ロジック（リトライ/429 等）
- `src/scrapers/comment_aggregator.py` - 個別コメント集約ロジック
- `src/scrapers/parsers/` - (将来的に) race/training/pedigree 用のパーサ分割
- ユニットテスト: `tests/test_fetcher.py`, `tests/test_comment_aggregator.py`

## スコープ
- 含む: fetch/aggregate ロジックの抽出、`keibabook.py` の委譲ラッパーの作成、基本的な単体テスト
- 含まない: UI、Exporter、外部API の大幅な変更

## スケジュール / マイルストーン
- M1 (1 day): fetcher と comment_aggregator の抽出とユニットテスト
- M2 (2 days): parsers の分割と統合テスト
- M3 (1 day): CI の更新、ドキュメント整理

## タスク一覧（Responsible / Status / Due）
- [ ] 抽出: fetcher.py の実装（AA） — todo — Due: 2025-12-08
- [ ] 抽出: comment_aggregator.py の実装（AA） — todo — Due: 2025-12-08
- [ ] テスト: fetcher 単体テスト（AA） — todo — Due: 2025-12-08
- [ ] テスト: aggregator 単体テスト（AA） — todo — Due: 2025-12-08
- [ ] 統合: keibabook.py のラッパー更新と検証（AA） — todo — Due: 2025-12-09

## リスクと回避策
- API 変更による壊滅的な後方互換性 → 小さなコミットに分け、テストを追加
- 非同期依存のバグ → `pytests` と `playwright` のモックで E2E テスト

## 検証と受け入れ条件
- 既存の呼び出しが破壊されない
- ユニットテストが新旧ともに動作している
- `keibabook.py` の内容が読みやすくなったこと

## 関連資料/チケット
- Issue: #123 keibabook 分割作業
- PR: TBA
