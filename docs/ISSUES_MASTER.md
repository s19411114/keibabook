# ---
# Title: Issues Master
# Category: issues
# Status: guide
# ---

# ISSUES_MASTER — Centralized Tasks, Bug Reports, and Improvements

このファイルはプロジェクトのすべての課題（バグ、設計変更、改善提案、作業タスク）を1つの場所にまとめた中央台帳です。

目的:
- すべてのエージェントがタスク・バグをここに追記する
- 完了した作業は `docs/archived/` に移動し、`PROJECT_LOG.md` に要約を追加する
- ドキュメントのスタイルは `docs/AGENT_ONBOARDING.md` のガイドラインに従う

---

## 構成ルール（必読）
1. 新規課題は「カテゴリ/短い見出し」の形式で追加する
2. 課題は「ステータス: TODO / IN_PROGRESS / DONE」で管理する
3. 重要な変更や設計は `AGENT_RULES.md`、`HANDOVER.md` にも同じ見出しで変更を記載する
4. 完了したら `scripts/archive_doc.py` を使って `docs/archived/` に移動する

---

## カテゴリ一覧
- BUG: バグ報告
- TASK: 実装タスク
- DESIGN: 設計・リファクタ提案
- DOC: ドキュメント更新
- PERF: パフォーマンス調査

---

## 例 (テンプレート)
- BUG: Fix bare excepts in src/utils/odds_db.py
  - reporter: opuser
  - status: TODO
  - priority: P1
  - notes: Replace bare except with `except Exception as e` and log

- TASK: Refactor app.py into ui/tabs/*
  - reporter: alice
  - status: IN_PROGRESS
  - priority: P2
  - notes: Create `src/ui/tabs/scraping_tab.py`, `tracking_tab.py` and move code incrementally

---

## 参考・移行元


## Implementation Plan (Migrated from implementation_plan.md.resolved)

Below is a consolidated summary and prioritized action list migrated from `implementation_plan.md.resolved`.

### Key Findings
- Critical: 9 instances of bare `except:`; multiple backup `.bak` files; `requirements.txt` formatting issues
- Medium: overly conservative 429 backoff, rate limiter defaults setting too high, duplicated checks across `check_*.py` files
- Improvements: add type hints, introduce `pydantic` for models, add structured logging, CI pipeline

### Priority Action Plan
1. Fix bare `except` usages and add explicit `Exception as e` logging
2. Remove `.bak` backup files and add pre-commit / CI lint to prevent future backups
3. Normalize `requirements.txt` formatting
4. Remove stale references to Docker in docs
5. Refactor `app.py` and `keibabook.py` into modularized UI and scraping modules
6. Expand tests (rate limiter, performance, error handling)
7. Add `PerfLogger` and CI integration for performance tests

### Notes
- Tasks above should be tracked in this `ISSUES_MASTER.md` with appropriate `status:` and `priority:` fields for each issue.
- On completion, use `scripts/archive_doc.py --move <file>` to move the original or related specs to `docs/archived/` and ensure `PROJECT_LOG.md` is updated.

### Historic Details (see archived doc for full content)
- The full implementation_plan.md.resolved has been migrated to `docs/archived/implementation_plan.md.resolved`.

## HANDOVER_TASKS (Migrated from issues/HANDOVER_TASKS.md)

These are time-consuming tasks intended for handover to other agents. Short summary:
- Docker environment optimization (DEPRECATED for this repo; review only) — performance improvements for Playwright images.
- run_pedigree.py non-blocking refactor (aiohttp + asyncio.Semaphore) — for high-volume pedigree fetch.
- Expand test suite for rate-limiting and performance tests.
- Logging and monitoring improvements (PerfLogger pattern outlined).

Notes:
- The full `issues/HANDOVER_TASKS.md` content has been archived at `docs/archived/archived-<timestamp>-HANDOVER_TASKS.md` (moved via script).
- Assign these tasks directly into this ISSUES_MASTER and add `status:` and `assignee:` lines to track.

## Archived Items (Docker-related scripts and shortcuts)
The following Docker-related scripts have been archived and are no longer part of recommended dev workflow (we use `.venv`):
- `scripts/start_dev.sh` -> docs/archived/archived-20251207T134432Z-start_dev.sh
- `scripts/start_dev.ps1` -> docs/archived/archived-20251207T134432Z-start_dev.ps1
- `scripts/start_dev.cmd` -> docs/archived/archived-20251207T134432Z-start_dev.cmd
- `start_app.bat` -> docs/archived/archived-20251207T134432Z-start_app.bat
- `create_shortcut.bat` -> docs/archived/archived-20251207T134432Z-create_shortcut.bat
- `scripts/create_shortcut.ps1` -> docs/archived/archived-20251207T134432Z-create_shortcut.ps1

Notes:
- These files are kept in `docs/archived/` for historical reference only. DO NOT use them for routine development unless explicitly required and documented.
- If a file needs to be re-enabled for a specific workflow, move it back and add a note in `ISSUES_MASTER.md` with the reason and reviewer approval.
- Improvements: type hints, Pydantic, logs, CI/CD, doc generation

## 2025-12-08 Gemini Code Review Findings

以下は [docs/REVIEW_20251208_gemini.md](file:///home/u/projects/TEST/keibabook/docs/REVIEW_20251208_gemini.md) の要約です。

### BUGS

- BUG/bare-except: `src/scrapers/keibabook.py` 等に bare except 使用箇所あり
  - reporter: gemini_agent
  - status: PARTIAL (keibabook.py主要2箇所修正済み、他ファイルは残存)
  - priority: P2
  - notes: `except Exception as e` に変更し、ログに詳細出力

- BUG/unused-base-url: `keibabook.py` で同じ base_url 計算が2回実行
  - reporter: gemini_agent
  - status: TODO
  - priority: P3

### DESIGN

- DESIGN/scrape-method-complexity: `scrape()` メソッドが約400行・深いネスト
  - reporter: gemini_agent
  - status: TODO
  - priority: P2
  - notes: 小さなヘルパメソッドに分割推奨

- DESIGN/app-tab-inconsistency: `app.py` のタブ分離が不完全
  - reporter: gemini_agent
  - status: TODO
  - priority: P3
  - notes: 全タブを `src/ui/` に分離して一貫性確保

### IMPROVE

- IMPROVE/bak-cleanup: `.bak` ファイルが残存（4件）
  - reporter: gemini_agent
  - status: DONE (2025-12-08 gemini_agent)
  - priority: P1
  - notes: 3件削除済み、`.gitignore` に既に *.bak あり

- IMPROVE/type-hints: 型ヒント追加推奨
  - reporter: gemini_agent
  - status: TODO
  - priority: P3

- IMPROVE/pydantic-models: Pydantic モデル導入検討
  - reporter: gemini_agent
  - status: TODO
  - priority: P3

- IMPROVE/structured-logging: 構造化ログ導入検討
  - reporter: gemini_agent
  - status: TODO
  - priority: P3

### BUG-003: ログイン認証の信頼性問題

- reporter: gemini_agent
- status: PARTIAL (CSSセレクタ修正済み、認証情報設定は要確認)
- priority: P1
- severity: High
- date: 2025-12-08
- files affected:
  - `src/utils/keibabook_auth.py` (主要認証ロジック)
  - `src/utils/login.py` (基本ログインクラス)
  - `src/scrapers/keibabook.py` (認証呼び出し)

**根本原因**:
1. 馬の数でログイン判定（6頭以上=成功）は少頭数レースや開催日外で誤検出
2. CSSセレクタ `table.syutuba` と実際の `table.syutuba_sp` の不一致
3. Cookie失効時の再ログインができない（`settings.yml` の `login_id/login_password` が空）
4. エラー時のログ情報が不十分

**推奨修正**:
- 認証情報を環境変数 (`LOGIN_ID`, `LOGIN_PASSWORD`) で設定
- CSSセレクタに `table.syutuba_sp tbody tr` を追加
- 認証確認方法を馬の数からログアウトリンク等の存在確認に変更検討

**関連ドキュメント**: [ログイン問題バグ調査レポート](file:///home/u/.gemini/antigravity/brain/4265f8df-30be-4a64-943e-dc9cd47bdc9b/implementation_plan.md)

---

## Templates & Workflow
Use the files under `docs/templates/` to standardize new docs and tasks. Key templates:
- `docs/templates/implementation_plan.md` — 実装計画 / Milestones
- `docs/templates/bug_template.md` — バグ報告のテンプレート（Status, Reporter, Severity）
- `docs/templates/task_template.md` — タスクのテンプレート（Assignee, Due）
- `docs/templates/handover_template.md` — 引き継ぎ向けテンプレート
 
運用ルールのまとめ:
1. 新しい設計/バグ/タスクは `docs/` に作成する。
2. ステータスは YAML front-matter（Status: draft/open/review/resolved/closed）で管理する。
3. 完了（Status: closed/resolved）にしたら `scripts/archive_docs.py --confirm` を使って `docs/archived/` に移動する。
4. `PROJECT_LOG.md` にアーカイブの要約が自動で追加される。手順は `scripts/archive_doc.py` を使用。

例: タスクを作るときは `docs/task-YYYYMMDD-short-title.md` を `docs/templates/task_template.md` から作成し、`Status: todo` で作業を開始、完了後 `Status: closed` を入れてアーカイブする。

---

## 運用ルール（例）
1. 日次作業: 今日やるタスクはステータスを `IN_PROGRESS` および `assignee: <name>` で更新
2. レビュー前: PRを作るときは引用リンクをこのISSUES_MASTERに追加
3. マージ後: ステータスを `DONE` にし、`scripts/archive_doc.py --move <path>` を実行

---

## 履歴 (履歴は `docs/archived/` に毎回移動してください)

---

## これからの課題・改善提案

### DOC/consolidation: ドキュメント統合ルールの改善

- reporter: gemini_agent
- status: TODO
- priority: P2
- date: 2025-12-08

**問題点**:
現状、同じ情報が複数ファイルに分散している:
1. `ISSUES_MASTER.md` にバグの詳細
2. `docs/bug-*.md` に同じバグの詳細（重複）
3. `REVIEW_*.md` にもバグリストあり

**改善案**:
1. **ISSUES_MASTER.md を唯一の台帳として使用** - すべてのバグ/タスク情報をここに集約
2. **個別ファイル (bug-*.md等) は作成しない** - ISSUES_MASTERに直接追記
3. **レビュー文書は発見のみ記録** - 詳細はISSUES_MASTERへリンク
4. **Templates & Workflow セクションの更新** - 上記ルールを明記

**エージェント向けルール追記案**:
```
新規課題はISSUES_MASTER.mdに直接追記する。
個別のbug-*.md, task-*.mdファイルは作成しない。
レビュー文書からはISSUES_MASTERへリンクで参照する。
```
