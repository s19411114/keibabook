
#### IMPROVE/migration-bak-cleanup: migration/backups の .bak ファイル

- reporter: gemini_agent
- status: DONE (2025-12-08)
- priority: P3
- date: 2025-12-08

**発見されたファイル**:
```
migration/backups/netkeiba_db_scraper.py.from_main.bak
migration/backups/netkeiba_result.py.from_main.bak
migration/backups/netkeiba_result_working_modification.py.bak
```

**対応内容**:
- `scripts/cleanup_migration_backups.sh` を追加し、該当 .bak ファイルをアーカイブして削除しました
- `scripts/install_prevent_bak_hook.sh` による `.bak` ファイルのコミット防止用フックを追加しました（READMEやdev手順に沿って利用してください）

**備考**:
- `migration/backups/` ディレクトリ内のバックアップはマイグレーションの作業履歴であるため、不要なファイルはアーカイブして削除するポリシーを適用しました。


ArchivedAt: 20251208T052700ZZ

#### BUG/unused-base-url: `keibabook.py` の base_url 重複計算

- reporter: gemini_agent
- status: DONE (2025-12-08 raptormini)
- priority: P3
- date: 2025-12-08
- resolved: `__init__` で `self.base_url` として一度計算し、以降は再利用


ArchivedAt: 20251208T052700ZZ
