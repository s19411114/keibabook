#!/usr/bin/env python3
"""
generate_migration_index.py
Generate migration/ARCHIVE_INDEX.md by scanning migration/ and migration/backups/.

Usage: python scripts/generate_migration_index.py
"""
import hashlib
import os
from pathlib import Path
from datetime import datetime


def sha1_of_file(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def scan_dir(root: Path):
    rows = []
    for p in sorted(root.rglob('*')):
        if p.is_file():
            stat = p.stat()
            try:
                display_path = p.relative_to(Path.cwd())
            except Exception:
                display_path = p
            rows.append({
                'path': display_path,
                'size': stat.st_size,
                'sha1': sha1_of_file(p),
                'mtime': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    return rows


def generate_index(out_path: Path):
    root = Path('migration')
    lines = ["# Migration / Backups Index\n"]
    lines.append(f"Generated: {datetime.now().isoformat()}\n")
    for sub in ['to_keiba_ai', 'backups']:
        p = root / sub
        if not p.exists():
            continue
        lines.append(f"## {sub}\n")
        rows = scan_dir(p)
        if not rows:
            lines.append("(No files found)\n")
            continue
        for r in rows:
            lines.append(f"- **{r['path']}** — {r['size']} bytes — {r['mtime']} — {r['sha1']}\n")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text('\n'.join(lines), encoding='utf-8')


def main():
    out_path = Path('migration/ARCHIVE_INDEX.md')
    generate_index(out_path)
    print(f'Wrote {out_path}')


if __name__ == '__main__':
    main()
