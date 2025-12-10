#!/usr/bin/env python3
"""
mem_watchdog.py - simple memory watcher/killer for Linux/WSL

- Monitors total system memory utilization (RSS + swap influence via available memory)
- When threshold exceeded, finds top memory-consuming processes and attempts to gracefully stop them
- Use with caution: only suitable as a last-resort safeguard (prefer limiting memory per-process or reduce memory usage)

Usage:
  python scripts/mem_watchdog.py --threshold 85 --names playwrigh|python --interval 2 --nprocs 1

Options:
  --threshold INT (default 85): system mem% threshold (>=) that triggers kill
  --threshold is recommended at 85% in development environments
  --names STR (default empty): process name pattern(s) separated by comma to target (e.g., python,playwright,chromium)
  --nprocs INT (default 1): number of top consumers to target per check
  --interval INT (default 2): seconds between checks
  --grace INT (default 10): seconds to wait after SIGTERM before SIGKILL
  --dry-run: do not actually kill, only log

Requires: psutil
"""
import argparse
import logging
import os
import signal
import sys
import time
from typing import List

try:
    import psutil
except Exception as e:
    print("Missing dependency 'psutil'. Install via 'pip install psutil'")
    raise

logger = logging.getLogger('mem_watchdog')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--threshold', type=int, default=85, help='System memory percent threshold to trigger (recommended 85%)')
    p.add_argument('--names', type=str, default='', help='Comma-separated process name patterns to prefer targeting (e.g., python,playwright)')
    p.add_argument('--nprocs', type=int, default=1, help='Number of processes to target when threshold exceeded')
    p.add_argument('--interval', type=float, default=2.0, help='Seconds between checks')
    p.add_argument('--grace', type=int, default=10, help='Grace period (seconds) after SIGTERM before SIGKILL')
    p.add_argument('--dry-run', action='store_true', help='Do not actually kill processes; only log actions')
    p.add_argument('--min-available-mb', type=int, default=200, help='Minimum available memory to keep (MB)')
    return p.parse_args()


def get_top_consumers(names_filter: List[str], n:int) -> List[psutil.Process]:
    procs = []
    for p in psutil.process_iter(attrs=['pid','name','exe','cmdline','memory_info']):
        try:
            mem = p.info.get('memory_info')
            rss = mem.rss if mem else 0
        except Exception:
            rss = 0
        if names_filter:
            name = (p.info.get('name') or '').lower()
            if not any(nf in name for nf in names_filter):
                continue
        procs.append((rss, p))
    procs.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in procs[:n]]


def safe_terminate(proc: psutil.Process, grace:int, dry_run:bool=False):
    try:
        logger.info(f"Attempting to terminate {proc.pid} {proc.name()} ({proc.exe() if proc.exe() else ''})")
    except Exception:
        logger.info(f"Attempting to terminate PID {proc.pid}")
    if dry_run:
        return True
    try:
        proc.send_signal(signal.SIGTERM)
    except Exception as e:
        logger.warning(f"SIGTERM send failed: {e}")
    # wait for process to die
    try:
        proc.wait(grace)
        logger.info(f"Process {proc.pid} terminated cleanly")
        return True
    except psutil.TimeoutExpired:
        logger.warning(f"Process {proc.pid} did not exit; sending SIGKILL")
        try:
            proc.kill()
            proc.wait(5)
            logger.info(f"Process {proc.pid} killed")
            return True
        except Exception as e:
            logger.error(f"Failed to kill {proc.pid}: {e}")
            return False


def human_size(num:int):
    for unit in ['B','KB','MB','GB','TB']:
        if num < 1024:
            return f"{num:.0f}{unit}"
        num = num/1024.0
    return f"{num:.0f}PB"


def main():
    args = parse_args()
    names_filter = [n.strip().lower() for n in args.names.split(',') if n.strip()]
    threshold = args.threshold
    interval = args.interval
    nprocs = max(1, args.nprocs)
    grace = args.grace
    dry_run = args.dry_run
    min_avail_bytes = args.min_available_mb * 1024 * 1024

    logger.info(f"Starting mem_watchdog: threshold={threshold}%, names={names_filter or '<any>'}, nprocs={nprocs}, interval={interval}s, dry_run={dry_run}")
    try:
        while True:
            mem = psutil.virtual_memory()
            used_pct = mem.percent  # percent used of total physical memory
            avail_bytes = mem.available
            logger.debug(f"Mem: used {used_pct}% available {human_size(avail_bytes)}")
            # Trigger on either percentage or low available bytes
            if used_pct >= threshold or avail_bytes < min_avail_bytes:
                logger.warning(f"Memory threshold exceeded: used {used_pct}% available {human_size(avail_bytes)}")
                # find top consumers - prefer names if provided, otherwise check top system consumers
                candidates = get_top_consumers(names_filter, nprocs if names_filter else nprocs)
                if not candidates and not names_filter:
                    # fallback to absolute top system consumers
                    all_procs = []
                    for p in psutil.process_iter(attrs=['pid','name','memory_info']):
                        try:
                            rss = p.info['memory_info'].rss
                        except Exception:
                            rss = 0
                        all_procs.append((rss,p))
                    all_procs.sort(key=lambda x: x[0], reverse=True)
                    candidates = [p for _, p in all_procs[:nprocs]]
                if not candidates:
                    logger.warning("No candidate processes found to kill")
                else:
                    logger.info(f"Targeting {len(candidates)} processes for termination")
                    for proc in candidates:
                        if proc.pid == os.getpid():
                            logger.info("Skipping self")
                            continue
                        safe_terminate(proc, grace, dry_run=dry_run)
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info('Exiting mem_watchdog (KeyboardInterrupt)')
    except Exception as e:
        logger.exception(f"Error in mem_watchdog: {e}")


if __name__ == '__main__':
    main()
