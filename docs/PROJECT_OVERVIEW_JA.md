# プロジェクト概要（日本語）

このドキュメントは、repo の主要ファイルの置き場所と最重要ファイル（requirements.txt など）について簡潔に説明します。

- `requirements.txt`: ルートにあり、Python の依存関係を管理します。環境の再現にはこのファイルを使います。
- 仮想環境: `.venv/`（ワークスペースルート） — 開発用の仮想環境がここにあります。通常は保存しない (gitignore に登録)。
- スクリプト: `scripts/` フォルダにツール、CLI、バックアップやリセットなどの補助ツールが入っています。
- メインのコード: `src/` にアプリケーションのロジック（スクレイパー、ユーティリティなど）
- ドキュメント: `docs/` に運用方針、データ取得方針、テンプレート等
- テスト: `tests/` に単体テスト
- データ: `data/` に取得した JSON を保存（通常は大きくなるので.gitignore の対象）
- デバッグ・HTML: `debug_files/` に Playwright/スクレイピング結果の HTML を保存

重要ファイルの場所:
- `requirements.txt` → ルート
- `.vscode/settings.json` → VS Code のローカル設定
- `README.md`, `docs/` → 運用方針や全体像

備考:
- 重要ファイル（機密な設定など）は `config/settings.yml` などで管理し、必要なら `secrets` 管理を使用してください。環境変数で `LOGIN_ID` や `LOGIN_PASSWORD` を渡して実行することもあります。
- 何を保存すべきか: 依存関係は `requirements.txt`、実行用の指示は `README.md`、保守用のタスクは `docs/` にまとめておくと良いです。

叩き台: もしよければ `docs/` に `MAINTENANCE.md` を追加して、日常の作業と重要ファイルのリストを作りましょう。
