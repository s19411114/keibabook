## keibabook → keiba-ai Migration summary (short)

Generated: 2025-12-08

### Files / features moved to migration (keiba-ai candidate)
- `src/scrapers/netkeiba_result.py` → migration/to_keiba_ai/src/scrapers/netkeiba_result.py
- `src/scrapers/netkeiba_db_scraper.py` → migration/to_keiba_ai/src/scrapers/netkeiba_db_scraper.py
- `src/utils/track_bias.py` → migration/to_keiba_ai/src/utils/track_bias.py
- `src/ui/track_bias_tab.py` → migration/to_keiba_ai/src/ui/track_bias_tab.py
- Pedigree ingestion and batch harvesting:
  - run_pedigree.py, run_pedigree_safe.py
  - pedigree_queue.json, pedigree_queue_small.json
  - pedigree_store/ (archives)
  - pedigree_access_check.py

### Other migration candidates / unused or heavy features
- `run_pedigree.py` / `run_pedigree_safe.py` (long-running batches) — candidate for asynchronous harvesting in keiba-ai.
- `pedigree_*` queues & store (large on-disk state) — move to shared storage in keiba-ai when possible.
- `netkeiba_db_scraper.py` / `netkeiba_result.py` (moved) — already in migration.
- `track_bias` analyzer (moved) — migration copy present.
- `app.py.complete_tab3` and `app_nicegui.py` — duplicate UI files; consider archiving or consolidating.
- `scripts/test_login.py` collides with `tests/test_login.py` — rename or convert to a non-test script if it's only for manual debugging.
- `.bak` files: some leftover backups are in `docs/archived/` and `migration/backups/` — consider cleaning and adding pre-commit to block committed backups.

### Notes and recommendations
- Keep `netkeiba_calendar.py` in main; it's small, lightweight, and required for scheduling (per user request). If you require an API instead, add keiba-ai API later.
- For heavy batch migration, add `keiba_ai_adapter` in main to call keiba-ai for result/pedigree/batch data.
- For migration completeness, add minimal test coverage under migration to ensure keiba-ai ingestion logic works (CI and tests moved accordingly).

If you want, I can:
- (A) Add a short migration note to `docs/` and `PROJECT_LOG.md` (done in other docs);
- (B) Add `keiba_ai_adapter` placeholder in `src/adapters/` and update callers to use it (safe shim);
- (C) Archive `app.py.complete_tab3` and `app_nicegui.py` in `docs/archived/`.
