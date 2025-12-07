#!/usr/bin/env python3
"""
Archive documentation files into docs/archived with timestamped name and append to PROJECT_LOG.md

Usage:
  python scripts/archive_doc.py <path/to/doc> [--move]

If --move is provided, the source file will be moved (deleted) after copying to the archive.
"""
import argparse
import shutil
from pathlib import Path
from datetime import datetime
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_DIR = PROJECT_ROOT / 'docs' / 'archived'
PROJECT_LOG = PROJECT_ROOT / 'PROJECT_LOG.md'


def archive_file(src: Path, move=False):
    if not src.exists():
        print(f"File not found: {src}")
        return False

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    dest_name = f"archived-{ts}-{src.name}"
    dest = ARCHIVE_DIR / dest_name
    shutil.copy2(src, dest)
    if move:
        src.unlink()

    # Append to PROJECT_LOG.md
    with open(PROJECT_LOG, 'a', encoding='utf-8') as f:
        f.write(f"\n- Archived {src} as {dest_name} at {ts}Z\n")
    print(f"Archived {src} -> {dest}")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='Path to file to archive')
    parser.add_argument('--move', action='store_true', help='Delete source file after archiving')
    args = parser.parse_args()

    src = Path(args.path)
    if src.is_absolute():
        # only allow within project
        if PROJECT_ROOT not in src.parents and src != PROJECT_ROOT:
            print('Path must be inside repository')
            return
    else:
        src = (Path.cwd() / src).resolve()

    archive_file(src, move=args.move)


if __name__ == '__main__':
    main()
