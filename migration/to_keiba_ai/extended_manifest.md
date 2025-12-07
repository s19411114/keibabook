# Extended Migration Manifest (2025-12-06)

This manifest expands the earlier manifest by listing additional files that are candidates to be moved or adapted to keiba-ai.

## Category: Netkeiba historical / archive
- src/scrapers/netkeiba_db_scraper.py - (move) Historical Netkeiba DB scraper (Results/Horse/Peds/Return)
- src/scrapers/netkeiba_result.py - (move) Result page parser + track-bias calc
- src/scrapers/netkeiba_calendar.py - (move) Calendar fetcher for scheduling
- src/scrapers/netkeiba_result.py - (move) Result page parser + track-bias calc
- src/scrapers/netkeiba_result.py -> `TrackBiasAnalyzer` references

## Category: Track bias calculation and analytics
- src/utils/track_bias.py - (move) Analytics: TrackBiasAnalyzer (unit-testable and core for keiba-ai)
- data/track_bias (dir) - store for output; consider moving storage to keiba-ai DB or shared bucket

## Category: Pedigree harvesting (batch)
- run_pedigree.py - (move) long running sequential batch (needs async/queue)
- run_pedigree_safe.py - (move) safe variant (better heuristics)
- pedigree_queue.json / pedigree_queue_small.json - (move) example queues
- pedigree_store/ - (move) store for saved pedigree JSON (or migrate to central storage)
- pedigree_access_check.py - (move) test/debug helper for pedigree access
- scripts/run_single_race.py - (adapter) may need changes for skip flags and to call keiba-ai API for historical

## Category: Scripts that rely on Netkeiba scheduler/historical
- scripts/cli_minimal_odds.py - (move/adapter) uses NetkeibaCalendarFetcher; can be adapted to call keiba-ai schedule API
- scripts/cli_prepare_now.py - (adapter) currently uses Netkeiba calendar and has `--full` to collect pedigree/past results; adapt to keiba-ai
- scripts/show_schedule.py - (move/adapter) uses NetkeibaCalendarFetcher for display
- scripts/debug_schedule.py & debug_schedule.py - (move) schedule debugging scripts using NetkeibaCalendarFetcher
- scripts/scrape_worker.py - (review) background worker; may need to delegate historical calls to keiba-ai

## Category: Tests & CI
- tests/test_netkeiba_calendar.py - (update) point tests to use keiba-ai or keep unit tests for keiba-ai's calendar module
- tests/test_scraper.py - (update) adjust expectations when keiba-ai becomes the authoritative store
- test_pedigree_access.py - (update) may be migrated to keiba-ai's test suite

## Category: Docs/Issues referencing migration
- docs/DATA_SOURCES.md - (updated) shows Netkeiba migration policy
- docs/DATA_STRATEGY.md - (updated) shows policy and rationale
- issues/HANDOVER_TASKS.md - (review) includes run_pedigree async migration tasks
- issues/OPUS_HAIKU_HANDOVER.md - (review) discusses 429 and related performance

## Category: Misc / Helpers
- src/scrapers/httpx_scraper.py - (review) general fetcher pattern used across scrapers
- src/utils/login.py - (adapter) shared login for keibabook private content; keep within keibabook
- src/utils/odds_db.py - (review) may be keiba-ai or shared
- src/utils/exporter.py - (adapter) output format to be compatible with keiba-ai's requirements

## Suggested Actions
- Move files grouped by functional area to keiba-ai in one PR per area.
- After keiba-ai implements APIs or ingestion pipelines, adapt `cli_prepare_now.py` / `cli_minimal_odds.py` to fetch historical data via keiba-ai.
- Add an adapter `src/adapters/keiba_ai_adapter.py` in keibabook to centralize calls to keiba-ai (or fallback to local scraping in exceptional situations).
- Update tests: split unit tests for keiba-ai modules and keep keibabook tests limited to per-race logic and keibabook-only fields.

## Notes
- Files copied into `migration/to_keiba_ai` are kept as-is with `MIGRATION COPY` header for review.
- This manifest should be used to coordinate PRs and hand-over tasks across the teams.

