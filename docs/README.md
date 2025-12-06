# docs/

このディレクトリはプロジェクトの設計、運用手順、データソース、仕様、FAQなどのドキュメントを格納します。

構成の例:
- `docs/templates/` : ドキュメント作成テンプレート
- `docs/archived/` : 解決済み、アーカイブ対象のドキュメント（履歴）
- `docs/README.md` : このファイル（ドキュメント運用ルール）
- その他: `DATA_SOURCES.md`, `VENUE_GUIDE.md` などカテゴリ別のドキュメント

ドキュメントのワークフロー（推奨）:
1. 新規の設計・提案は `docs/` に `design-<short-name>.md` として作成し、先頭に `Status: draft` を記載します。
2. バグ報告は `issues/` に `bug-<id>-title.md` を作成して `Status: open` を付与します。
3. 修正・議論を経て `Status: resolved` または `Status: closed` になったものは `docs/scripts/archive_docs.py` を使って `docs/archived/` に移動します（手動でも可）。

ドキュメントのテンプレートやアーカイブ基準は `docs/templates/` と `docs/ARCHIVE_GUIDE.md` を参照してください。

この方針をプロジェクト全体で統一することで、重複を減らし、レビュー可能で検索しやすい資料を維持します。
