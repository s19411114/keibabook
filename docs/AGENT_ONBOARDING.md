# AIエージェント向けオンボーディング（AGENT_ONBOARDING.md）

このファイルは、AIエージェントや開発者がプロジェクトにスムーズに参加し、同じ手順で運用できるように階層化、チェックリスト、ルーチンをまとめたものです。

## 目的
- ドキュメントと実行ルーチンを 1 つの場所にまとめる
- AI が読みやすい簡潔なセクション構成にする
- 作業を終えたらアーカイブの場所へ移動する運用を定める

---

## 1. 最初に読むべきファイル（Quick Start）
- `AGENT_RULES.md` - 最優先。必ず守る作業ルール
- `docs/AGENT_ONBOARDING.md` - このファイル（まとめ）
- `HANDOVER.md` - 高レベルの背景と最近の変更
- `DEV_GUIDE.md` - 開発手順およびローカルセットアップ

---

## 2. 準備（短時間でできるチェック）
1. `pwd` でプロジェクトルートを確認（例: /home/u/ドキュメント/GeminiCLI/TEST/keibabook）
2. `.venv` をアクティベート

```bash
source .venv/bin/activate
python --version  # 3.12.x を期待
```

3. 依存関係を確認

```bash
pip install -r requirements.txt  # (必要に応じて)
```

4. `PYTHONPATH` を調整せず、スクリプトは `scripts/` から起動すること（ただし CLI 実行時はプロジェクトルート内から起動）

---

## 3. 代表的なルーチン（ルーチン化）
### スモークチェック（簡単な確認）
- `scripts/agent_health_check.py` を実行し、JSON ベースの要約を得る

```bash
python scripts/agent_health_check.py --output health.json
```

- 追加の軽量検査（手動）:
  - `scripts/open_logged_in_browser.py` を実行して `cookies.json` を読み込み、tk cookie を確認する
  - `scripts/test_login.py` を実行してクッキーがページに反映されるかチェック（既知のレースID を使う）

### スクレイピングの流れ
1. `scripts/run_single_race.py --venue 東京 --race 11` などを使い、1 レースを取得して JSON を確認
2. 成功なら `data/` 以下にファイルができる


---

## 4. ドキュメントの更新ルール（必ず守る）
1. 新しい設計・作業手順・バグレポート・解決した内容は、`docs/` 内で更新する
2. 確認済み・完了した作業は `docs/archived/` に移動する（ファイル名プレフィックス `archived-YYYYMMDD-<desc>.md`）
3. ドキュメントは必ず `PROJECT_LOG.md` に要約を残す（誰が何をいつやったか）
4. 重要変更は `AGENT_RULES.md` と `HANDOVER.md` に反映する

---

## 5. AI 向けメタ情報（機械可読）
- 参照する `agent_manifest.yml` を使って、AI が自動的に実行できるルーチンと検査基準を定義しておくこと

---

## 6. 引き継ぎのチェックリスト
- [ ] 環境の準備手順が `DEV_GUIDE.md` にあること
- [ ] `AGENT_RULES.md` が最新であること
- [ ] 主要手順（スクレイピング・ログイン・テスト）が `scripts/` にあること
- [ ] テスト用の既知レース ID のリストが `tests/` か `data/` にあること
- [ ] 変更履歴が `PROJECT_LOG.md` にまとめられていること

---

## 7. 今後やること（短期）
- `agent_manifest.yml` にエントリを追加して `health_check` と主要コマンドを登録
- `scripts/agent_health_check.py` を定期実行して結果を JSON に出力
- ドキュメントの階層化とアーカイブの運用方法を `HANDOVER.md` に記載

---

## 8. 連絡先・レビュープロセス
- PR は `feat/*` または `fix/*` のプレフィックスで作成
- WIP の変更は `git stash` か WIP ブランチで管理する
- レビューには `debug_files/` のスクショや HTML を添付

---

このファイルは、`AGENT_RULES.md` と `HANDOVER.md` を補完するための集中ドキュメントです。AI が自動読込する場合、`agent_manifest.yml` を参照してください。
