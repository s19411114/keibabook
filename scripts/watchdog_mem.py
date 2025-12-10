#!/usr/bin/env python3
"""
Memory watchdog for development environments.

This script monitors system memory usage and takes action when thresholds exceed.

Features:
- Observe total/available memory using psutil
- If system memory use > system-threshold (%), find large processes and try to stop them gracefully
- Can target processes by PID, name, or find top-N memory users
- Dry-run option prints actions but does not kill
- Logs to stdout and optional logfile

Usage examples:
    # Monitor system memory and kill top user if mem% > 85
    python scripts/watchdog_mem.py --system-threshold 85 --max-kill 1

    # Monitor and kill processes by name if they exceed 50% of total system memory
    python scripts/watchdog_mem.py --per-process-name bigprocess:50

This utility is intended for development or small lab usage; for production use systemd/cgroups.
"""
from __future__ import annotations
import argparse
import logging
import os
import signal
import sys
import time
from typing import Dict, List, Optional, Tuple

try:
    import psutil
except Exception:
    psutil = None


logger = logging.getLogger('watchdog_mem')


def parse_proc_spec(spec: str) -> Tuple[str, float]:
    """Parse "name:percent" spec or "pid:mb" style.
    Returns (key, threshold) where threshold is percent (0-100) or MB when key is 'pid'
    """
    if ':' not in spec:
        return spec, 0.0
    key, val = spec.split(':', 1)
    try:
        return key, float(val)
    except Exception:
        return key, 0.0


def find_processes_by_name(name: str) -> List[psutil.Process]:
    if not psutil:
        return []
    procs = []
    for p in psutil.process_iter(['name', 'pid']):
        try:
            if p.info.get('name') == name or os.path.basename(p.info.get('name') or '') == name:
                procs.append(p)
        except Exception:
            continue
    return procs


def top_memory_users(n: int = 3) -> List[psutil.Process]:
    if not psutil:
        return []
    procs = list(psutil.process_iter(['name', 'pid', 'memory_info']))
    procs_sorted = sorted(procs, key=lambda p: (p.info.get('memory_info').rss if p.info.get('memory_info') else 0), reverse=True)
    return procs_sorted[:n]


def kb(v: int) -> str:
    return f"{v/1024:.1f}KB" if v < 1024*1024 else f"{v/1024/1024:.1f}MB"


def check_and_act(system_threshold: float, per_process: List[str], max_kill: int, grace: int, dry_run: bool, logfile: Optional[str]):
    if not psutil:
        raise SystemExit('psutil required; install it with `pip install psutil`')
    vm = psutil.virtual_memory()
    used_pct = vm.percent
    if logfile:
        with open(logfile, 'a', encoding='utf-8') as f:
            f.write(f"[{time.ctime()}] mem {vm.total} total - {vm.available} avail - {used_pct}% used\n")
    logger.info(f"Memory: {used_pct}% used (available {kb(vm.available)})")
    to_kill: List[psutil.Process] = []
    if used_pct >= system_threshold:
        logger.warning(f"System memory threshold exceeded ({used_pct} >= {system_threshold})")
        # find targets
        # If per_process contains entry like name:percent, check those
        for spec in per_process:
            name, thr = parse_proc_spec(spec)
            try:
                if name.isdigit():
                    pid = int(name)
                    p = psutil.Process(pid)
                    rss = p.memory_info().rss
                    # thr interpreted as MB when using pid:mb
                    if thr and (rss / (1024*1024)) >= thr:
                        to_kill.append(p)
                else:
                    procs = find_processes_by_name(name)
                    for p in procs:
                        rss = p.memory_info().rss
                        if thr and (rss / (vm.total) * 100.0) >= thr:
                            to_kill.append(p)
            except Exception as e:
                logger.debug(f"Error checking spec {spec}: {e}")
        if not to_kill:
            # Fallback: kill top n
            to_kill = top_memory_users(max_kill)
    # Now perform kills
    killed = 0
    for p in to_kill:
        if killed >= max_kill:
            break
        try:
            name = p.name()
            rss = p.memory_info().rss
            logger.warning(f"Selected to stop PID {p.pid} ({name}) rss={kb(rss)})")
            if dry_run:
                logger.info(f"[dry-run] would SIGTERM {p.pid}")
            else:
                p.terminate()
                try:
                    p.wait(timeout=grace)
                    logger.info(f"PID {p.pid} terminated")
                except psutil.TimeoutExpired:
                    logger.warning(f"PID {p.pid} did not exit in {grace}s; sending SIGKILL")
                    p.kill()
                killed += 1
        except psutil.NoSuchProcess:
            continue
        except Exception as e:
            logger.exception(f"Failed to action PID: {e}")
    if logfile:
        with open(logfile, 'a', encoding='utf-8') as f:
            f.write(f"[{time.ctime()}] actions taken: {killed}\n")


def main(argv=None):
    p = argparse.ArgumentParser(description='Memory watchdog: monitor system memory and stop processes')
    p.add_argument('--interval', type=float, default=5.0, help='Check interval in seconds')
    p.add_argument('--system-threshold', type=float, default=85.0, help='System used memory percent threshold to trigger action (recommended 85%)')
    p.add_argument('--per-process', action='append', default=[], help='Per-process spec like name:percent or pid:mb')
    p.add_argument('--max-kill', type=int, default=1, help='Maximum number of processes to target when triggered')
    p.add_argument('--grace', type=int, default=10, help='Grace time (seconds) before SIGKILL')
    p.add_argument('--logfile', type=str, default=None, help='Optional logfile path (append)')
    p.add_argument('--dry-run', action='store_true', help='Do not actually kill processes')
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    try:
        while True:
            try:
                check_and_act(args.system_threshold, args.per_process, args.max_kill, args.grace, args.dry_run, args.logfile)
            except Exception as e:
                logger.exception(f"watchdog check failed: {e}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info('Shutting down watchdog')


if __name__ == '__main__':
    main()
