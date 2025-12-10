Category: Documentation
Status: Archived

# ---
# Title: Document Archive Guide
# Category: process
# Status: guide
# ---

# ドキュメント・アーカイブ ガイドライン

このファイルは、ドキュメントやバグレポートのアーカイブ手順を示します。

基本ルール:
- Status: closed / resolved / archived のいずれかを先頭に記載します。
- 自動アーカイブは `scripts/archive_docs.py` を使用して行います（dry-run 実行で確認）。
 - 既存のファイル単位のアーカイブには `scripts/archive_docs.py` を使用します。
 - `docs/ISSUES_MASTER.md` 内の完了済みセクション（`Status: DONE/closed/resolved` を含む）を個別セクションで抽出してアーカイブする場合は `scripts/extract_completed_from_issues_master.py` を使用します。
- 重要な設計決定や古い仕様は `docs/archived/` に移動し、元のファイルへ `ArchivedAt:` のメタ情報を追加します。

手動アーカイブ (例):
1. ファイルを開いて先頭に `Status: closed` を追加する。
2. `python scripts/extract_completed_from_issues_master.py` で検出を確認（dry-run はデフォルト動作）
3. `python scripts/extract_completed_from_issues_master.py --confirm` を実行して、該当セクションを `docs/archived/completed_issues.md` に追記し、`PROJECT_LOG.md` に自動追記します
 5. CI: `Weekly Archive Dry-Run` workflow will run every Monday and open an issue when it detects completed sections. Review the issue and trigger the `Manual Archive` workflow if you want to confirm the archive.

スクリプトは移動後に `ArchivedAt: YYYY-MM-DD` を追加します。

新しいスクリプト:

1. `python scripts/extract_completed_from_issues_master.py --dry-run` で検出を確認
2. `python scripts/extract_completed_from_issues_master.py --confirm` を実行して、該当セクションを `docs/archived/issues_master` に移動し、`PROJECT_LOG.md` にサマリーを追記します
