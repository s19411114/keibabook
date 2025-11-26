#!/usr/bin/env python3
"""Delete oldest debug/temp files in a project until the total size is under a threshold.
Usage: scripts/cleanup_size_limit.py --dir <project_dir> --max-mb <MB> [--force]
"""
import argparse
import sys
from pathlib import Path
import fnmatch
import os
from typing import List, Tuple


def find_matching_files(root: Path, patterns: List[str]) -> List[Tuple[float, int, Path]]:
    files = []
    for p in root.rglob("*"):
        if p.is_file():
            for pat in patterns:
                if fnmatch.fnmatch(p.name, pat):
                    try:
                        stat = p.stat()
                        files.append((stat.st_mtime, stat.st_size, p))
                    except Exception:
                        continue
                    break
    return files


def human_mb(nb: int) -> str:
    return f"{nb / 1024 / 1024:.2f}MB"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".", help="Project directory to scan")
    parser.add_argument("--max-mb", type=float, default=50.0, help="Maximum MB of matching files")
    parser.add_argument("--force", action="store_true", help="Actually delete files")
    args = parser.parse_args()

    root = Path(args.dir).resolve()
    if not root.is_dir():
        print(f"Directory not found: {root}", file=sys.stderr)
        sys.exit(2)

    patterns = ["debug_*", "bench_*", "*.tmp", "*tmp_*", "pp_*", "playwright_test.py", "*.log"]
    files = find_matching_files(root, patterns)
    total = sum(size for _, size, _ in files)

    print(f"Found {len(files)} matching files, total size {total} bytes ({human_mb(total)})")
    threshold_bytes = int(args.max_mb * 1024 * 1024)
    if total <= threshold_bytes:
        print("Under threshold; nothing to do.")
        return

    # Sort oldest first
    files.sort(key=lambda x: x[0])
    removed = 0
    for mtime, size, path in files:
        if total <= threshold_bytes:
            break
        if args.force:
            try:
                path.unlink()
                print(f"Removed: {path} ({size} bytes)")
            except Exception as e:
                print(f"Failed to remove {path}: {e}")
        else:
            print(f"[DRY-RUN] Would remove: {path} ({size} bytes)")
        total -= size
        removed += 1

    print(f"Final total: {total} bytes ({human_mb(total)}), files processed: {removed}")
    if not args.force:
        print("Run with --force to actually delete files")


if __name__ == "__main__":
    main()
