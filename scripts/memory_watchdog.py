#!/usr/bin/env python3
"""
memory_watchdog.py
Simple watchdog to monitor overall memory use and terminate or restart a target process
when the system memory usage exceeds a threshold.

Usage:
  python scripts/memory_watchdog.py --threshold 85 --action terminate --process-name scrape_worker.py --grace 10

Notes:
- Requires `psutil` to run (install in .venv: `pip install psutil`).
- On WSL, kernel OOM logs may require `dmesg` with admin privileges to inspect.
"""
import argparse
import logging
import os
import signal
import time
from typing import Optional

try:
    import psutil
except Exception:
    psutil = None

logger = logging.getLogger('memory_watchdog')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


def find_process_by_name(name: str) -> Optional[psutil.Process]:
    if psutil is None:
        raise RuntimeError('psutil is required')
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if proc.info.get('name') and name in proc.info.get('name'):
                return proc
            cmdline = proc.info.get('cmdline') or []
            if any(name in str(part) for part in cmdline):
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def safe_terminate(proc: psutil.Process, grace_seconds: int = 10) -> None:
    try:
        logger.info(f"Sending SIGTERM to PID {proc.pid} ({proc.name()})")
        proc.send_signal(signal.SIGTERM)
        start = time.time()
        while proc.is_running() and time.time() - start < grace_seconds:
            time.sleep(0.5)
        if proc.is_running():
            logger.info(f"Sending SIGKILL to PID {proc.pid} ({proc.name()})")
            proc.send_signal(signal.SIGKILL)
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        logger.warning(f"Could not signal process: {e}")


def get_memory_percent() -> float:
    if psutil is None:
        raise RuntimeError('psutil is required')
    return psutil.virtual_memory().percent


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--threshold', type=float, default=85.0, help='System memory percent threshold to act on (recommended 85%)')
    p.add_argument('--action', choices=['terminate', 'notify'], default='terminate', help='Action to perform when threshold is exceeded')
    p.add_argument('--process-name', default='scrape_worker.py', help='Process name substring to find and act on')
    p.add_argument('--interval', type=float, default=5.0, help='Polling interval seconds')
    p.add_argument('--grace', type=int, default=10, help='Grace seconds before SIGKILL after SIGTERM')
    p.add_argument('--once', action='store_true', help='Exit after first action')
    args = p.parse_args()

    if psutil is None:
        logger.error('psutil missing - please install in your environment (pip install psutil)')
        raise SystemExit(2)

    logger.info(f"Memory watchdog starting - threshold={args.threshold}%, interval={args.interval}s, proc_name={args.process_name}")
    acted = False
    try:
        while True:
            mem = get_memory_percent()
            if mem >= args.threshold:
                logger.warning(f"Memory usage high: {mem}% >= {args.threshold}%")
                proc = find_process_by_name(args.process_name)
                if proc:
                    if args.action == 'terminate':
                        safe_terminate(proc, grace_seconds=args.grace)
                        acted = True
                    else:
                        logger.warning(f"Threshold exceeded but action=notify, process PID {proc.pid}")
                else:
                    logger.warning(f"No process found with name containing: {args.process_name}")
                if args.once:
                    break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info('Exiting (KeyboardInterrupt)')


if __name__ == '__main__':
    main()
