#!/usr/bin/env python3
"""
Add minimal frontmatter (Category/Status) to docs and top-level docs files
for files that are missing them. This updates files in-place.
Usage:
  python scripts/add_doc_frontmatter.py --yes
  python scripts/add_doc_frontmatter.py --dry-run
"""
from pathlib import Path
import argparse

# Mapping of known docs to categories and status (fallbacks used otherwise)
DOC_CATEGORIES = {
    'AGENT_RULES.md': ('Operational', 'Active'),
    'README.md': ('Overview', 'Active'),
    'DEV_GUIDE.md': ('Development', 'Active'),
    'WORKFLOW.md': ('Process', 'Active'),
    'HANDOVER.md': ('Handover', 'Active'),
    'PROJECT_LOG.md': ('Operational', 'Active'),
    'ARCHITECTURE.md': ('Architecture', 'Active'),
    'ARCHIVE_README.md': ('Documentation', 'Archived'),
    'ARCHIVE_GUIDE.md': ('Documentation', 'Archived'),
    'LOCAL_RACING_GUIDE.md': ('Guide', 'Active'),
    'COOKIE_EXPORT_GUIDE.md': ('Guide', 'Active'),
    'DATA_SOURCES.md': ('Reference', 'Active'),
    'ISSUES_MASTER.md': ('Operational', 'Active'),
    'INDEX.md': ('Index', 'Active'),
}


def has_key(lines, key):
    for ln in lines[:40]:
        if ln.strip().lower().startswith(key.lower() + ':'):
            return True
    return False


def add_frontmatter(path: Path, category: str, status: str, dry_run: bool):
    txt = path.read_text(encoding='utf-8')
    lines = txt.splitlines()
    modified = False

    add_lines = []
    if not has_key(lines, 'Category'):
        add_lines.append(f'Category: {category}')
        modified = True
    if not has_key(lines, 'Status'):
        add_lines.append(f'Status: {status}')
        modified = True

    if modified:
        new_txt = '\n'.join(add_lines + [''] + lines)  # add blank line after frontmatter
        if dry_run:
            print(f'[DRY RUN] Would add to {path}:')
            for l in add_lines:
                print('  ' + l)
        else:
            path.write_text(new_txt, encoding='utf-8')
            print(f'Updated {path} with: {add_lines}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', default='.', help='Repo root')
    parser.add_argument('--yes', action='store_true', help='Apply changes')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed')
    args = parser.parse_args()

    base = Path(args.path)
    docs_dir = base / 'docs'
    if not docs_dir.exists():
        print('No docs directory found')
        raise SystemExit(1)

    targets = list(docs_dir.rglob('*.md'))
    # also include top-level docs
    for p in base.glob('*.md'):
        targets.append(p)

    # filter out archived and templates
    targets = [p for p in targets if 'archived' not in p.parts and 'templates' not in p.parts]

    for p in sorted(targets):
        name = p.name
        category, status = DOC_CATEGORIES.get(name, ('Guide', 'Active'))
        if args.dry_run or args.yes:
            add_frontmatter(p, category, status, dry_run=args.dry_run)
        else:
            print(p)

    print('Done.')
