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
- 重要な設計決定や古い仕様は `docs/archived/` に移動し、元のファイルへ `ArchivedAt:` のメタ情報を追加します。

手動アーカイブ (例):
1. ファイルを開いて先頭に `Status: closed` を追加する。
2. `scripts/archive_docs.py --dry-run` で検出されるか確認する。
3. 検出されたら `scripts/archive_docs.py` を実行して `docs/archived` に移動する。

スクリプトは移動後に `ArchivedAt: YYYY-MM-DD` を追加します。
