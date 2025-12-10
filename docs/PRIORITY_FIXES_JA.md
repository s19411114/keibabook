Category: Guide
Status: Active

# 優先修正項目（短期）

現在の目的: 最小機能を回復して、2週間以上止まっている状態から復旧する。

短期優先 (短期間で改善できるもの):
1. **ログイン問題の修復**
   - `src/utils/login.py` を確認して、cookie のロード/保存と `ensure_logged_in()` の処理フローをテストする。
   - `scripts/test_login.py` を実行して現況を確認する。cookie が期限切れなら再ログインして cookies.json を更新。
   - テスト後、スクレイパー（`KeibaBookScraper`）が正常に動くか手動で検証する。

2. **最小スケジュール取得の保証**
   - `scripts/cli_prepare_now.py` が内部で `KeibaTodayFetcher` と `NetkeibaCalendarFetcher` のフォールバックを行うようになっているので、これが常に失敗していないか確認する。
   - まずは `--fast` モードを使い、`skip_pedigree` と `skip_past_results` を True にして、最小限の情報だけ保存する流れを確認する。

3. **手動ワークフロー（簡易）**
   - 自動スクレイピングが失敗している期間は、手動で `scripts/cli_prepare_now.py --fast` を実行して必要データを取得し、アプリの基本機能を回復する。

4. **ログ収集と再現手順**
   - `logs/` と `debug_files/` をチェックして、失敗時のスクレイピングログ（`scraper_log.txt`）や HTML（`debug_files/`）を収集する。

5. **中長期での改善案**
   - 重いバッチ処理（`run_pedigree`, `netkeiba_db_scraper`）は keiba-ai に移管予定。keibabook に残すのは per-race JSON 抽出のみ。
   - 非同期化・並列化（`run_pedigree` の aiohttp 化） などの改善は keiba-ai 側で行う。

実行コマンド例（環境有効化）:
```
source .venv/bin/activate
python3 scripts/test_login.py
python3 scripts/cli_prepare_now.py --fast
```

必要なら、私が `scripts/test_login.py` の修正や `scripts/backup_repo.sh` の実行、`KeibaBookLogin` の追加診断を行います。どれを優先しますか？