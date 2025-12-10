#!/usr/bin/env python3
"""
Run a command with a soft address-space memory limit (RLIMIT_AS) applied.

Usage:
  python scripts/run_with_mem_limit.py --mem-mb 1024 -- python -c "a=' ' * (500*1024*1024)"

Notes:
  - Works on Unix-like systems; on Linux it sets RLIMIT_AS for the child process.
  - For better isolation on modern Linux, systemd cgroups are preferred.
"""
from __future__ import annotations
import argparse
import resource
import subprocess
import sys
import os
import shlex


def set_limits(mem_mb: int):
    # RLIMIT_AS is the virtual memory size limit in bytes
    mem_bytes = mem_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))


def main(argv=None):
    p = argparse.ArgumentParser(description='Run a command with a memory limit (MB)')
    p.add_argument('--mem-mb', type=int, required=True, help='Memory limit in MB for the command')
    p.add_argument('cmd', nargs=argparse.REMAINDER, help='Command to run')
    args = p.parse_args(argv)
    if not args.cmd:
        raise SystemExit('No command specified')
    # Convert to string array if needed
    cmd = args.cmd
    if cmd[0] == '--':
        cmd = cmd[1:]
    # Execute with preexec_fn to set RLIMIT_AS
    try:
        returncode = subprocess.call(cmd, preexec_fn=lambda: set_limits(args.mem_mb))
        sys.exit(returncode)
    except Exception as e:
        print('Error:', e)
        sys.exit(1)


if __name__ == '__main__':
    main()
