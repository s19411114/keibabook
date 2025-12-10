---
Title: Memory Management and Watchdog
Category: ops
Status: guide
---

# Memory Management & Watchdog

This doc explains strategies and tooling for managing memory usage during development and running the scrapers.

## Immediate: revert/adjust WSL settings
- If you previously applied `.wslconfig` changes (e.g. memory=4GB, swap=2GB) and experienced OOM, revert or adjust them.
- On the Windows host, edit `%USERPROFILE%\.wslconfig` then run `wsl --shutdown` to apply.

Example `.wslconfig` revert snippet (set memory unlimited):

```
[wsl2]
memory=8GB  # increase if needed or remove to allow unlimited
processors=2
swap=4GB
autoMemoryReclaim=gradual
```

**Note:** WSL autoMemoryReclaim and swap settings only take effect after `wsl --shutdown`.

## Granular options
- Use `scripts/run_with_mem_limit.py` to start a process with an address-space RLIMIT: `python scripts/run_with_mem_limit.py --mem-mb 1024 -- python run_scraper.py`.
- Use systemd / cgroups on Linux to set `MemoryMax=` for per-service memory limits.
- For one-off, use `prlimit` or `ulimit` (bash) wrappers where applicable.

## Watchdog
We include `scripts/watchdog_mem.py` – a development watchdog that periodically monitors memory and optionally terminates the top consumers when the system threshold is exceeded.

Usage examples:

```
# 1) Dry-run to see what would be killed when > 85%
python scripts/watchdog_mem.py --system-threshold 85 --dry-run --interval 5

# 2) Run and kill at most 2 processes if > 90% (optional different policy)
python scripts/watchdog_mem.py --system-threshold 90 --max-kill 2

```

### Integrations and Security
- On servers prefer to run under systemd with a unit that sets `MemoryMax` and restart policy.
- Watchdog is intended for development environments only; production should use cgroup limits and proper monitoring/alerts.

## Recommended workflow
1. Add safe RLIMIT/cgroup in your process runner in production (recommended `MemoryMax=4G` for scrapers).
2. Use `run_with_mem_limit.py` during heavy local testing to set limit and avoid OOM (recommended 4G per `scrape_worker`).
3. If occasional memory surges occur, start `watchdog_mem.py` to protect your environment (recommended system threshold 85%).
