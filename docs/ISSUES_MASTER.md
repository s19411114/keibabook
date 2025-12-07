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

---

## 運用ルール（例）
1. 日次作業: 今日やるタスクはステータスを `IN_PROGRESS` および `assignee: <name>` で更新
2. レビュー前: PRを作るときは引用リンクをこのISSUES_MASTERに追加
3. マージ後: ステータスを `DONE` にし、`scripts/archive_doc.py --move <path>` を実行

---

## 履歴 (履歴は `docs/archived/` に毎回移動してください)

