# PR 作成と機能分割ガイド（日本語）

1. 小さく切り出す
- 単一の大きなファイルを一度に移すのではなく、機能で分割してください（例: カレンダー、DBスクレイパー、トラックバイアス、ペディグリー収集）。

2. フォルダ化
- 機能ごとにフォルダを作る（例: `netkeiba_calendar/`, `netkeiba_archive/`, `track_bias/`, `pedigree/`）。
- 各フォルダに `README.md` と `tests/` を入れる。

3. 依存性を明示する
- 元の `requirements.txt` に記載がある外部パッケージは、移行するコード側でも最小限の依存に留める。

4. 互換レイヤー（Adapter）
- keibabook 側は `src/adapters/keiba_ai_adapter.py` を追加し、keiba-ai に移管された機能を呼び出すための単純な関数を提供する。

5. 移行の手順（提案）
- `git checkout -b migration/xxx`（ローカルでまとめて確認）
- `scripts/backup_repo.sh` を実行して一時バックアップを作る
- 機能を分割・整理して `migration/to_keiba_ai/` にコピーする（MIGRATION COPY ヘッダを付ける）
- `migration/to_keiba_ai/manifest.md` を更新して、対象と rationale を明示する
- keiba-ai 側の PR 作成を行う（keiba-ai 側へは1機能ずつ PR を出すべき）

6. PR の本文テンプレ（日本語）
- 概要: 何を移管するか
- 理由: なぜ keiba-ai に移管するか（重複／バッチ処理負荷／保守性改善）
- 依存: 必要な外部ライブラリ・設定
- テスト: どうやって手元で動かすかの手順
- 注意: keibabook 側の adapter 変更点

