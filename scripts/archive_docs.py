#!/usr/bin/env python3
"""
Archive docs and issue files marked as resolved/closed into docs/archived/

Usage:
  python scripts/archive_docs.py --dry-run
  python scripts/archive_docs.py --confirm
"""
import argparse
from pathlib import Path
import re
import shutil
from datetime import datetime


def detect_status(file_path: Path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for ln in range(20):
                line = f.readline()
                if not line:
                    break
                m = re.match(r'^Status:\s*(\S+)', line, re.IGNORECASE)
                if m:
                    return m.group(1).lower()
        return None
    except Exception:
        return None


def archive_file(file_path: Path, dest_dir: Path, dry_run: bool = True):
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / file_path.name
    if dry_run:
        print(f"[DRY-RUN] Would move {file_path} -> {dest_file}")
        return True
    # Move and annotate
    shutil.move(str(file_path), str(dest_file))
    try:
        with open(dest_file, 'a', encoding='utf-8') as f:
            f.write(f"\nArchivedAt: {datetime.now().isoformat()}\n")
        print(f"Archived {file_path} -> {dest_file}")
        return True
    except Exception as e:
        print(f"Archive failed for {dest_file}: {e}")
        return False


def main(dry_run: bool = True, path: Path = Path('.')):
    candidates = []
    # Scan top-level docs and issues
    scan_dirs = [path / 'docs', path / 'issues']
    for sd in scan_dirs:
        if not sd.exists():
            continue
        for p in sd.rglob('*.md'):
            # skip templates and archived dir
            if 'templates' in str(p.parts) or 'archived' in str(p.parts):
                continue
            status = detect_status(p)
            if status in ('closed', 'resolved', 'archived'):
                candidates.append(p)

    if not candidates:
        print('No files to archive.')
        return 0

    print('Candidates to archive:')
    for c in candidates:
        print('-', c)

    if dry_run:
        print('\nDry run mode. To execute archives, run with --confirm')
        return 0

    # perform archive
    for c in candidates:
        # preserve directory structure
        rel = c.relative_to(path / 'docs') if (path / 'docs') in c.parents else c.relative_to(path / 'issues')
        dest_dir = path / 'docs' / 'archived' / rel.parent
        archive_file(c, dest_dir, dry_run=False)

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--confirm', action='store_true', help='Execute archival (not dry-run)')
    parser.add_argument('--path', default='.', help='Workspace root')
    args = parser.parse_args()
    main(dry_run=not args.confirm, path=Path(args.path))
