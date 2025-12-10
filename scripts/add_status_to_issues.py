#!/usr/bin/env python3
"""
Add missing Status/Category to issue files under issues/.
Usage:
  python scripts/add_status_to_issues.py --yes
  python scripts/add_status_to_issues.py --dry-run
"""
from pathlib import Path
import argparse

ISSUE_DIR = Path('issues')


def has_key(lines, key):
    for ln in lines[:30]:
        if ln.strip().lower().startswith(key.lower() + ':'):
            return True
    return False


def add_frontmatter(path: Path, dry_run: bool):
    txt = path.read_text(encoding='utf-8')
    lines = txt.splitlines()
    modified = False
    add_lines = []
    if not has_key(lines, 'Category'):
        add_lines.append('Category: Issue')
        modified = True
    if not has_key(lines, 'Status'):
        add_lines.append('Status: Active')
        modified = True
    if modified:
        new_txt = '\n'.join(add_lines + [''] + lines)
        if dry_run:
            print(f'[DRY RUN] Would add to {path}:')
            for l in add_lines:
                print('  ' + l)
        else:
            path.write_text(new_txt, encoding='utf-8')
            print(f'Updated {path} with: {add_lines}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--yes', action='store_true')
    args = parser.parse_args()

    files = []
    if ISSUE_DIR.exists():
        files = list(ISSUE_DIR.rglob('*.md'))

    for p in files:
        if 'archived' in p.parts:
            continue
        if args.dry_run or args.yes:
            add_frontmatter(p, dry_run=args.dry_run)
        else:
            print(p)

    print('Done.')
