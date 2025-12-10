Category: Issue
Status: Active

# ClaudeOpus Full Summary — KeibaBook Scraper

This file consolidates the key information for external review (perf, behavior, tests, PR and reproduction instructions).

1) Current status summary
- Problem: Some scraping runs have taken a very long time (4+ hours reported). Observed behaviors include long wait/sleep periods, repeated fetch retries, or long-run batch jobs (pedigree queue). Some test cases also revealed brittle behavior in `KeibaBookScraper.scrape`.
- Recent changes (branch `fix/scraper-normalization-perf-debug`):
  - Venue normalization added to `src/utils/venue_manager.py` and used in schedule fetchers
  - Per-fetch perf logging and `debug_fetches_<race_key>.json` saved by `src/scrapers/keibabook.py`
  - `run_single_race.py`: added `--skip-debug-files` and normalized `venue` usage
  - Comment fetch concurrency safety (new page per concurrent task) in `KeibaBookScraper`
  - Test additions: `tests/test_venue_manager.py`, `tests/test_schedule_utils.py`, `tests/test_run_single_race.py`
  - Added `issues/claudeopus_request.md` and this file `issues/claudeopus_full_summary.md` (for external review)

2) Links & Artifacts
- Branch: `fix/scraper-normalization-perf-debug`
- PR URL: https://github.com/s19411114/keibabook/pull/new/fix/scraper-normalization-perf-debug
- Commit: recent commit id: `a19596184539f4b0f458ec41305266158230df48` (check `git log -1`)
- Important debug files are generated at run time if `skip_debug_files` is not set:
  - `debug_fetches_<race_key>.json` (JSON with fetch times and HTTP statuses)
  - `debug_page_<race_key>.html` (page HTML for a fetched page)
  - `data/` per-race JSON and odds snapshots

3) Test status (as of last local run)
- The repo tests were run during the patching/analysis process; many tests passed. One failing unit test was `tests/test_scraper.py::test_keibabook_scraper_scrape_method` related to page mock call expectations; this is a brittle test that uses `async_playwright` mocks and page instance identity checks.
- Recommendation: adapt the test to assert on `call(ANY, expected_url)` or inspect `mock_calls` more flexibly to avoid instance mismatch.

4) Primary suspected long-run causes (summarized)
- Frequent Playwright browser/process startups (launch cost)
- Reuse of a single `Page` for multiple parallel tasks causing navigation collisions & retries
- Exponential backoff with large waits (429 retries up to 300s) causing long stallups
- Scripts that intentionally wait until a scheduled time (e.g., `cli_minimal_odds.py` using `await asyncio.sleep(wait_seconds)`)
- High I/O volume writing debug files and CSVs — particularly in Docker/shared mounts
- Large queue batch scripts (`run_pedigree.py`) running sequentially

5) Reproduction steps & measurement commands
- Host (PowerShell):
  ```powershell
  $env:PYTHONPATH='C:\GeminiCLI\TEST\keibabook';
  Measure-Command { C:/path/to/python.exe scripts/run_single_race.py --venue 浦和 --race 9 --perf --skip-dup --full --skip-debug-files }
  ```
- Docker: 削除（非推奨）。代わりにホスト上での再現手順を実行してください。 See: `cd /path/to/keibabook; python3 -m venv .venv; source .venv/bin/activate; pip install -r requirements.txt; python scripts/run_single_race.py --venue 浦和 --race 9 --perf --skip-debug-files`
- Docker limited resources to test: add `--cpus` and `--memory` flags

6) Logs to attach for review
- `debug_fetches_<race_key>.json`
- `debug_page_<race_key>.html`
- `data/` last 20 files list with timestamps
- `docker logs` & `docker stats` if running in Docker
- the `settings.yml` used for runs
- `pedigree_queue.json` if running `run_pedigree.py` / `run_pedigree_safe.py` scripts

7) Priority fix suggestions (short-term, mid-term, long-term)
- Short-term (fast):
  - Use `--skip-debug-files` and `--fast` to test. Clamp `RateLimiter` base value, reduce exponential backoff max wait (e.g., 30s or 10s), and reduce Playwright timeout in `--fast` mode.
- Mid-term: 
  - Reuse a single browser for multiple race runs (already partially implemented) and ensure `Page` concurrency is handled with distinct pages or queue.
  - Write debug files conditionally and buffer writes to reduce I/O
- Long-term:
  - Introduce a robust queuing/worker model for batch tasks with progress and preemptive cancellation.
  - Add central tracing/perf collection and histogram of durations to identify worst performers.

8) Other notes
- ClaudeOpus (or any external reviewer) CANNOT access this chat conversation automatically. The reviewer only sees what is included in the repo/PR body and attached files. If you want to provide the chat transcript, paste it into this PR or attach it as a file. Otherwise, use the files in `issues/claudeopus_request.md` and this `issues/claudeopus_full_summary.md` to provide concise, direct instruction and the logs.

9) Suggested attachments for PR
- Attach sample `debug_fetches_<race_key>.json` and `debug_page_<race_key>.html` for a slow run.
- Attach a `docker stats` screenshot or `docker logs` tail output from the slow run.
- Provide the exact command lines you used and the `settings.yml` used in the run.

10) Next steps (for us)
- If you want, I can run a Host vs Docker comparison, collect debug logs, and attach them to the PR for ClaudeOpus. This requires Playwright browsers to be installed and network access.
- I can also add the conversation transcript into the PR body if you want the reviewer to read this entire chat.

--- End of summary