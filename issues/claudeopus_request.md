# ClaudeOpus Review Request — KeibaBook Scraper

SHORT SUMMARY
- The scraper has been observed to run for 4+ hours in some runs (report of being the longest to date). We're requesting a deep review focused on performance, robustness, and why long runs occur.

ENVIRONMENT
- Repo path: `C:\GeminiCLI\TEST\keibabook`
- Python 3.12+ (workspace uses 3.14) and Playwright (Chromium)
- Optionally runs inside Docker using `mcr.microsoft.com/playwright/focal` image
- Common test commands:
  - Host (PowerShell):
    ```powershell
    $env:PYTHONPATH='C:\GeminiCLI\TEST\keibabook';
    Measure-Command { C:/path/to/python.exe scripts/run_single_race.py --venue 浦和 --race 9 --perf --skip-dup --full --skip-debug-files }
    ```
  - Docker (Linux):
    ```sh
    docker run --rm -it -v "$(pwd)":/app -w /app mcr.microsoft.com/playwright/focal \
      /bin/bash -lc "python -m pip install -r requirements.txt && time python scripts/run_single_race.py --venue 浦和 --race 9 --perf --skip-dup --full --skip-debug-files"
    ```

KEY FILES TO REVIEW
- `src/scrapers/keibabook.py` (core scraper) — pay attention to scraping flows, page context reuse, `asyncio` usage
- `scripts/run_single_race.py` (runner) — how `race_id`/`race_key` and flags are built
- `scripts/cli_prepare_now.py` — CLI orchestration producing scheduled runs
- `src/utils/venue_manager.py` & `src/utils/schedule_utils.py` — normalization and ID generation
- `src/utils/rate_limiter.py` — throttling and backoff
- `run_pedigree.py` / `run_pedigree_safe.py` — potential long-running processes
- `scripts/cli_minimal_odds.py` — waiting for scheduled offsets
- `tests/*` and `tests/test_scraper.py` — check brittle test conditions

SUSPECTED PROBLEM AREAS (TO VERIFY)
1. Playwright browser startup overhead and repeated launches per-race when not necessary
2. Single `Page` instance reused incorrectly across parallel tasks (e.g., multiple comment fetches) causing race conditions
3. Docker resource limits and file I/O (debug files written per-race) causing slowdown
4. Exponential backoff on 429 responses leading to minutes-long waits per fetch
5. `cli_minimal_odds.py` and similar scripts that intentionally wait for scheduled time using `await asyncio.sleep(wait_seconds)` — valid but causes long-running processes
6. High-volume batch scripts (`run_pedigree.py`) processing large queues sequentially
7. Schedule normalization mismatches producing wrong `race_id` / `shutuba_url` and repeated 404/429
8. Logging / debug file writes in high volume that slow down containerized I/O

CHECKLIST & REPRO STEPS
1. Confirm running process and which script caused long execution:
   - Host: `Get-Process python` (PowerShell)
   - Docker: `docker ps`, `docker logs <id> --tail 200` and `docker stats <id>`
2. Run single-run perf test (Host & Docker) using the commands above; measure start-to-finish and `PERF` logs.
3. Collect debug artifacts created by the run:
   - `debug_fetches_<race_key>.json` (per-fetch details)
   - `debug_page_<race_key>.html` (last fetched page HTML)
   - `data/` folder last-modified files list
4. Examine `debug_fetches_<race_key>.json` for slow/failed fetches (status, goto_ms, content_ms, total_ms) and for 429 frequency
5. Check whether multiple browser launches are happening per run or browser is reused across multiple fetches
6. If Docker performance is suspected, run the same command on host and inside Docker to check the timing differences
7. For `run_pedigree.py` / `run_pedigree_safe.py`, compute the queue size in `pedigree_queue*.json` and estimate run time at current rate limiter settings

LOGS & ARTIFACTS TO ATTACH
- `debug_fetches_<race_key>.json` (if present) — per-fetch JSON with timing and HTTP status
- `debug_page_<race_key>.html` — the last page fetched for the race, if exists
- `data/` last 20 files (list and timestamps)
- `docker logs` output and `docker stats` summary (if Container used)
- copy of `settings.yml` and the command used to run the script
- optional: `pedigree_queue.json` (or small) if `run_pedigree*` was executed

QUESTIONS FOR CLAUDEOPUS (answer these in the review)
1. Which step(s) are dominating runtime? Provide top 3 culprits with evidence from logs
2. Is Docker adding significant overhead? If yes, suggest recommended Docker run flags or WSL settings
3. Is there a clear bug causing indefinite waits or large sleep durations that should be fixed? Which code block(s) require patching?
4. Short-term actionable fixes to reduce runtime immediately (prefer non-invasive changes)
   - e.g., modify `RateLimiter` caps, remove per-fetch file writes, reuse one browser/process, change backoff from exponential to limited linear
5. Mid- and long-term architecture improvements focusing on throughput without triggering site blocking
6. Suggested minimal changes to tests to prevent regressions and better detect long-running cases

OUTPUT EXPECTED FROM CLAUDEOPUS
- Prioritized list of fixes (short-term, mid-term, long-term)
- One or two small code patches if appropriate (e.g., 4-6 lines to clamp backoff, or change `asyncio.sleep` usages)
- Evidence from logs or rationale demonstrating why slow behavior occurs
- A testing checklist and reproducible steps to confirm the issues are fixed

ACCEPTANCE CRITERIA
- Identified root cause for 4+ hour run (or a reproducible scenario where the runtime is normal)
- One quick fix implemented (or specific patch recommended) that reduces run time significantly
- A plan for addressing larger architecture choices like parallelization vs site-block risks

If preferred, save this file as `issues/claudeopus_request.md` in the repository and attach the logs; that will make it easier to exchange with external reviewers.

--- End of request
