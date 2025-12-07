# Consolidation Suggestions for keiba-ai

This document suggests consolidation steps for the files gathered in migration/to_keiba_ai.

## Goal
- Move Netkeiba historical collectors, track-bias calculation, and batch pedigree harvesters to keiba-ai.
- Keep keibabook focused on per-race JSON generation and keibabook-specific fields.

## Suggested Consolidations
1. `src/scrapers/netkeiba_calendar.py` + `scripts/show_schedule.py` + `scripts/cli_minimal_odds.py` -> `keiba-ai/data_sources/netkeiba_calendar` (single service for scheduling and light polling)
2. `src/scrapers/netkeiba_db_scraper.py` + `src/scrapers/netkeiba_result.py` -> `keiba-ai/archive/netkeiba_db` (historical CSV/Parquet exports + DB ingestion)
3. `src/utils/track_bias.py` -> `keiba-ai/analytics/track_bias` (unit-tested module that can be used by other tools)
4. `run_pedigree.py`, `run_pedigree_safe.py`, `pedigree_queue*.json`, `pedigree_store/` -> `keiba-ai/batch/pedigree_harvester` (asynchronous, rate-limited harvesters with queueing support)
5. CLI / scheduling scripts (e.g., `cli_prepare_now.py` and `cli_minimal_odds.py`) that use Netkeiba historical data should be parameterized to call keiba-ai services instead of directly scraping Netkeiba DB.

## Notes for migration
- Keep the file header `MIGRATION COPY` and provenance in initial PR for easy review.
- Remove direct site scraping of `db.netkeiba.com` from keibabook once keiba-ai provides APIs or shared storage.
- Provide a minimal compatibility layer or a read-only adapter (`keibabook_netkeiba_adapter`) in keibabook to fetch prepared datasets from keiba-ai (e.g., `keiba_ai.get_historical(race_id)`).

## Tests
- Add unit tests for `TrackBiasAnalyzer` and result parsing after migration.
- Validate that per-race JSON in keibabook still includes `track_bias` (call keiba-ai service or locally compute if convenience is needed) but avoid keeping the Netkeiba scraping code in keibabook.

## Phasing
1. Copy code and tests to keiba-ai (migration PR)
2. Introduce adapter in keibabook to fetch historical results from keiba-ai (API or shared storage) and remove netkeiba DB scrapers
3. Remove heavy batch scripts from keibabook repo once keiba-ai is accepted and provides API/ingest

