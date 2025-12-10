#!/usr/bin/env python3
"""
mark_doc_read.py
Mark a document as read in migration/DOC_MANIFEST.json

Usage:
python scripts/mark_doc_read.py --path "docs/README.md" --actor "AI"
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

MANIFEST_PATH = Path('migration/DOC_MANIFEST.json')


def load_manifest():
    if not MANIFEST_PATH.exists():
        raise SystemExit('manifest not found; run scripts/generate_doc_manifest.py')
    with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_manifest(m):
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(m, f, ensure_ascii=False, indent=2)


def mark_read(path: str, actor: str):
    m = load_manifest()
    files = m.get('files', {})
    if path not in files:
        raise SystemExit(f'{path} not found in manifest')
    files[path]['read'] = True
    files[path]['read_by'] = actor
    files[path]['read_at'] = datetime.now().isoformat()
    m['files'] = files
    save_manifest(m)
    print(f'Marked {path} read by {actor}')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--path', required=True)
    p.add_argument('--actor', default='AI')
    args = p.parse_args()
    mark_read(args.path, args.actor)


if __name__ == '__main__':
    main()
