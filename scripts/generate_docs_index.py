#!/usr/bin/env python3
"""
Generate a simple docs/INDEX.md that lists all documentation files grouped by folder and status

Usage:
    python scripts/generate_docs_index.py --path /path/to/repo
"""
import argparse
from pathlib import Path
import re
import sys


def extract_meta(path: Path):
    meta = {'title': path.name, 'status': '', 'category': ''}
    try:
        with path.open('r', encoding='utf-8') as f:
            for _ in range(30):
                ln = f.readline()
                if not ln:
                    break
                m = re.match(r'^Title:\s*(.+)', ln, re.I)
                if m:
                    meta['title'] = m.group(1).strip()
                m = re.match(r'^Status:\s*(\S+)', ln, re.I)
                if m:
                    meta['status'] = m.group(1).strip()
                m = re.match(r'^Category:\s*(.+)', ln, re.I)
                if m:
                    meta['category'] = m.group(1).strip()
                # break early if we've got some info
                if meta['title'] != path.name and meta['status']:
                    break
    except Exception:
        pass
    return meta


def build_index(repo_root: Path):
    docs_dir = repo_root / 'docs'
    all_docs = []
    if docs_dir.exists():
        for p in sorted(docs_dir.rglob('*.md')):
            # skip archived dir and templates
            if 'archived' in p.parts or 'templates' in p.parts:
                continue
            meta = extract_meta(p)
            rel = p.relative_to(repo_root)
            all_docs.append((str(rel), meta))

    # Collect top-level docs (.md at root)
    root_docs = []
    for p in sorted(repo_root.glob('*.md')):
        if p.parts[-1].lower().startswith('readme'):
            continue
        meta = extract_meta(p)
        root_docs.append((str(p.relative_to(repo_root)), meta))

    out_lines = [
        '# Documentation Index',
        '',
        'This file is generated. Run `python scripts/generate_docs_index.py --confirm` to update.',
        '',
    ]

    if root_docs:
        out_lines.append('## Root docs')
        out_lines.append('')
        for path, meta in root_docs:
            out_lines.append(f'- **{meta["title"]}**: [{path}]({path})  {f"(Status: {meta['status']})" if meta['status'] else ''}')
        out_lines.append('')

    # Group docs by category if available
    category_map = {}
    for path, meta in all_docs:
        cat = meta.get('category') or 'Uncategorized'
        category_map.setdefault(cat, []).append((path, meta))

    for cat, docs in category_map.items():
        out_lines.append(f'## {cat}')
        out_lines.append('')
        for path, meta in docs:
            display = meta['title'] if meta['title'] else path
            status = f" (Status: {meta['status']})" if meta['status'] else ''
            out_lines.append(f'- **{display}**: [{path}]({path}){status}')
        out_lines.append('')

    # Write out
    out = repo_root / 'docs' / 'INDEX.md'
    if args.confirm:
        out.write_text('\n'.join(out_lines), encoding='utf-8')
        print('Written', out)
    else:
        print('\n'.join(out_lines))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', default='.', help='Repository root')
    parser.add_argument('--confirm', action='store_true', help='Write the index to disk')
    args = parser.parse_args()
    repo_root = Path(args.path)
    build_index(repo_root)
