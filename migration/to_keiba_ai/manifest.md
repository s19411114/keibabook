# Migration Manifest

This manifest lists files and folders selected for migration to the keiba-ai project, with a brief rationale for each.

## Scrapers and historical collection
- src/scrapers/netkeiba_calendar.py — Netkeiba calendar scraping (schedules)
- src/scrapers/netkeiba_db_scraper.py — Netkeiba DB scrapers for historical race/horse data
- src/scrapers/netkeiba_result.py — Netkeiba result parsing (historical results)

## Analytics and batch processing
- src/utils/track_bias.py — Track bias computation and helpers
- run_pedigree.py — Batch pedigree downloader (long-running, heavy)
- run_pedigree_safe.py — Safe variant for pedigree harvesting
- pedigree_queue.json — Example queue for pedigree processing
- pedigree_queue_small.json — Small example queue
- pedigree_store/ — Storage for downloaded pedigree HTML and records
- pedigree_access_check.py — Pedigree access diagnostic and HTML debug capture

## Scripts that rely on Netkeiba scheduling/history
- scripts/cli_minimal_odds.py — Uses Netkeiba calendar for odds
- scripts/cli_prepare_now.py — Uses Netkeiba calendar, can collect historical fields
- scripts/show_schedule.py — Netkeiba schedule display helper
- debug_schedule.py — Dev schedule fetcher/probing (uses Netkeiba)

## Documentation & Issues (hand-over related)
- docs/DATA_SOURCES.md — update to indicate Netkeiba historical sources move
- docs/DATA_STRATEGY.md — update to indicate Netkeiba DB migration
- issues/OPUS_HAIKU_HANDOVER.md — long-running scripts & run_pedigree discussions
- issues/HANDOVER_TASKS.md — run_pedigree async tasks
- issues/claudeopus_full_summary.md — analysis referencing historical batch jobs

## Notes and rationale
- These files and modules are either responsible for historical, cross-app data collection or heavy analytic tasks (track-bias) that are overlapping with keiba-ai's responsibilities.
- Keibabook should retain per-race JSON extraction logic and keibabook-specific fields (comments, keibabook-only metadata).
- We'll copy these files here in a migration bundle so keiba-ai maintainers can review and adopt them while minimizing disruption in keibabook.

