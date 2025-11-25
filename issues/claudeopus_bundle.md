# ClaudeOpus Bundle: KeibaBook Scraper — Single Attachment

This bundle consolidates the essential materials to hand off to an external reviewer (e.g., ClaudeOpus): summary, reproduction steps, and a sample log archive.

Files included in this bundle (already committed to branch `fix/scraper-normalization-perf-debug`):
- `issues/claudeopus_request.md` — compact review request and checklist.
- `issues/claudeopus_full_summary.md` — full context, file changes, PR link, and suspected causes.
- `issues/attachments/keibabook_sample_logs.zip` — sample logs/data for inspection (includes sample race JSONs and url_log.csv).

How to use this bundle
1. Pull the branch and open the PR: https://github.com/s19411114/keibabook/pull/new/fix/scraper-normalization-perf-debug
2. Inspect `issues/claudeopus_full_summary.md` for background & the list of suspected problem areas.
3. Extract the sample logs for concrete timing and URL examples:
   - `unzip issues/attachments/keibabook_sample_logs.zip -d /tmp/keibabook_sample_logs`
4. Run the reproduction command given in the summary and compare timing:
   - Host: `Measure-Command { ... scripts/run_single_race.py --venue 浦和 --race 9 --perf --skip-dup --full --skip-debug-files }`
   - Docker: `docker run ... mcr.microsoft.com/playwright/focal ...`

What else to provide to get the best advice
- Attach in PR or provide links to: `debug_fetches_<race_key>.json` and `debug_page_<race_key>.html` for the actual slow run if available (these were not present in local repo snapshot).
- Provide the `settings.yml`, exact CLI command used, the OS or Docker resource allocations (e.g., `--cpus`, `--memory`), and if run on host vs in Docker.
- If a long run occurred, provide `docker logs` and `docker stats` outputs for the run if Docker was used.

Notes about chat history
- The chat transcript is not automatically provided to reviewers. If you want them to review chat content, add a snippet or the full transcript to this bundle or PR comment.

Acceptance criteria
- Reviewer identifies the dominant causes of runtime slowness and provides prioritized fixes.
- If possible, attach a small patch (4-6 lines) with a quick fix (e.g. clamp backoff) and a plan for mid/long-term improvements.

---

If you want me to also commit the actual `debug_fetches` files or additional logs, I can do so (zip them and add to `issues/attachments`).
