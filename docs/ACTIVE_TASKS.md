# ACTIVE_TASKS.md

このファイルは現在進行中のタスク（今すぐやること、次にやること、完了）を保持します。
短く最新状況を更新しておくことで、誰でもすぐに「今なにをしているか」が把握できます。

ガイド:
- 1行に1タスク。
- ステータスは `todo`, `in-progress`, `blocked`, `review`, `done` のうちの一つ。
- 重要なタスクには `Owner`, `Due` を設定。

Format:
| Task | Owner | Status | Due | Notes |
|---|---:|---|---|---|
| Add docs templates and archive guide | u | done | 2025-12-06 | Added templates & script; pushed to branch refactor/debugfile-unify |
| Create doc standards and PROCESS.md | u | done | 2025-12-06 | Added docs/PROCESS.md |
| Migrate issues into docs/ templates | TBD | todo | 2025-12-10 | Manual review required; run `scripts/archive_docs.py` for candidate detection |
| Setup GitHub Issue/PR templates and Actions | TBD | todo | 2025-12-12 | Add .github/ISSUE_TEMPLATE and workflows to auto-archive/notify |

更新方法:
- 変更があるたびに `git commit -m "docs: update ACTIVE_TASKS"` して push してください。
