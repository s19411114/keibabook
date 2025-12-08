#!/usr/bin/env python3
"""
Check that docs have Category metadata in front matter.

Usage:
  python scripts/check_docs_metadata.py --path . --fail-on-missing
"""
import argparse
from pathlib import Path
import re
import sys


def has_category(path: Path) -> bool:
    try:
        with path.open('r', encoding='utf-8') as f:
            for _ in range(30):
                ln = f.readline()
                if not ln:
                    break
                if re.match(r'^Category:\s*', ln, re.I):
                    return True
    except Exception:
        return False
    return False


def main(repo_root: Path, fail_on_missing: bool):
    docs_dir = repo_root / 'docs'
    missing = []
    for p in sorted(docs_dir.rglob('*.md')):
        if 'archived' in p.parts or 'templates' in p.parts:
            continue
        if not has_category(p):
            missing.append(p)
    if missing:
        print('Documentation files missing Category metadata:')
        for p in missing:
            print('-', p)
        if fail_on_missing:
            return 1
    else:
        print('All docs include Category metadata or are excluded.')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', default='.', help='Repository root')
    parser.add_argument('--fail-on-missing', action='store_true', help='Return non-zero on missing')
    args = parser.parse_args()
    rc = main(Path(args.path), args.fail_on_missing)
    sys.exit(rc)
