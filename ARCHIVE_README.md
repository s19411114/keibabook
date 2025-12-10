Category: Documentation
Status: Archived

# Archive / Migration Index

This file describes the small tools to generate an archive index and to view it using the NiceGUI prototype.

Usage:

1. Generate index

```
python scripts/generate_migration_index.py
```

2. Launch NiceGUI prototype

```
python -m app_nicegui
```

3. In the NiceGUI UI, click left sidebar "📚 アーカイブ表示" to load `migration/ARCHIVE_INDEX.md`. Use the file input to open specific files under `migration/`.

This facility is intentionally minimal and read-only; it helps reviewers verify what was moved to `migration/to_keiba_ai/` and what backups exist in `migration/backups/`.

AI workflow and marking files:
- `scripts/generate_doc_manifest.py` makes `migration/DOC_MANIFEST.json` (list of files with 'read' status).
- To mark a file as read through automation after an AI agent processes it, run:
```
python scripts/mark_doc_read.py --path "docs/README.md" --actor "AI"
```
- NiceGUI provides a way to view unread files and mark them as read interactively.

AI best practice (recommended):
1. Run `python scripts/generate_doc_manifest.py` to refresh the document list.
2. Run `python scripts/ai_ingest_manifest.py --max_bytes 5000` to print (ingest) unread documents in a dry-run.
3. After processing each file's content, mark it read with `python scripts/mark_doc_read.py --path "..." --actor "AI-Agent"`.
4. Optionally, run `python scripts/ai_ingest_manifest.py --max_bytes 5000 --mark --actor 'AI-Agent'` to mark all unread files as read after reviewing (use with caution).

Notes:
- The manifest resets a file's `read` flag when the file's SHA1 changes, which helps detect updates and re-processing needs.
- The UI in `app_nicegui.py` provides a simple 'Unread Documents' control and a 'Mark as Read' action for interactive marking.

CI suggestion:
- Add `python scripts/generate_doc_manifest.py` to CI jobs to keep `migration/DOC_MANIFEST.json` updated for PRs that modify docs or `migration/`.

CI suggestion:
- Add `python scripts/generate_migration_index.py` to CI to always refresh `migration/ARCHIVE_INDEX.md` on main branch or PRs touching `migration/`.
- Optionally, publish `migration/ARCHIVE_INDEX.md` as an artifact or commit it back to the repo if the team prefers an always-updated index under source control.