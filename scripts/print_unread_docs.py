#!/usr/bin/env python3
"""
print_unread_docs.py
Print unread documents from migration/DOC_MANIFEST.json with optional truncation. Useful for AI agents to ingest content.

Usage: python scripts/print_unread_docs.py [--max_bytes 10000]
"""
import argparse
import json
from pathlib import Path

MANIFEST = Path('migration/DOC_MANIFEST.json')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--max_bytes', type=int, default=10000)
    args = p.parse_args()
    if not MANIFEST.exists():
        raise SystemExit('Run scripts/generate_doc_manifest.py first')
    m = json.loads(MANIFEST.read_text(encoding='utf-8'))
    files = m.get('files', {})
    unread = [k for k, v in files.items() if not v.get('read')]
    for path in unread:
        print('---')
        print('PATH:', path)
        try:
            txt = Path(path).read_text(encoding='utf-8')
            print(txt[:args.max_bytes])
            if len(txt) > args.max_bytes:
                print('\n... (truncated)')
        except Exception as e:
            print(f'Error reading {path}: {e}')


if __name__ == '__main__':
    main()
