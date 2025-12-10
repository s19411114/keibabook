Category: Guide
Status: Active

# ---
# Title: Documentation Process
# Category: process
# Status: guide
# ---

# ドキュメント運用プロセス

目的: ドキュメントの乱立を抑え、検索しやすく、レビュー可能な状態に保つための最小ルールです。

ルール（要点）:
- **1件1責任者**: ドキュメント（設計/手順/バグ）は少なくとも1名の責任者（Author）を記載すること。
- **Status フィールドの管理**: `Status: draft` → `Status: open/review` → `Status: resolved/closed` → `Archived`（自動/手動）
- **テンプレート利用**: 新規ドキュメント作成時は `docs/templates/` を利用する。
- **レビュー チェック**: 重要な設計は PR でレビュー、マージ時に `Status: accepted` を更新する。
- **アーカイブ**: `Status: closed`（または `resolved`）になったものは `scripts/archive_docs.py` で `docs/archived/` に移動する。

ベストプラクティス:
- ファイル名にプレフィックス `design-` / `howto-` / `bug-` を付け分類を強制する（例: `design-cache.md`, `bug-123-fetch-error.md`）。
- README（`docs/README.md`）に目次を保っておく。
- 既にあるドキュメントが似た内容をカバーしている場合、既存ファイルに補足するか、そのファイルを分割/マージして整理する。