#!/usr/bin/env python3
"""
Check docs/ and issues/ markdown files for the presence of a top-level `Status:` header
and report files lacking it.
"""
from pathlib import Path
import re


def detect_status(file_path: Path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for _ in range(10):
                line = f.readline()
                if not line:
                    break
                if re.match(r'^Status:\s*\w+', line, re.IGNORECASE):
                    return True
        return False
    except Exception:
        return False


def main():
    base = Path('.')
    dirs = [base / 'docs', base / 'issues']
    missing = []
    for d in dirs:
        if not d.exists():
            continue
        for p in d.rglob('*.md'):
            if 'templates' in p.parts or 'archived' in p.parts:
                continue
            if not detect_status(p):
                missing.append(p)

    if not missing:
        print('All docs/issues have Status header')
        return 0
    print('Files missing Status header:')
    for p in missing:
        print('-', p)
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
