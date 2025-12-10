#!/usr/bin/env python3
"""
ai_ingest_manifest.py
AI-friendly helper: prints unread files and optionally marks them as read after confirmation.

Usage:
  python scripts/ai_ingest_manifest.py --max_bytes 5000 [--mark] [--actor AI]
"""
import argparse
import json
from pathlib import Path
from subprocess import run, CalledProcessError

MANIFEST = Path('migration/DOC_MANIFEST.json')


def print_unread(max_bytes=5000):
    m = json.loads(MANIFEST.read_text(encoding='utf-8'))
    files = m.get('files', {})
    unread = [k for k, v in files.items() if not v.get('read')]
    for path in unread:
        p = Path(path)
        print('---')
        print('PATH:', path)
        try:
            txt = p.read_text(encoding='utf-8')
            print(txt[:max_bytes])
            if len(txt) > max_bytes:
                print('\n... (truncated)')
        except Exception as e:
            print('Error reading', path, e)
    return unread


def mark_read(path: str, actor: str):
    # Always call via python3 to ensure permissions/exec bits are not needed
    run(['python3', 'scripts/mark_doc_read.py', '--path', path, '--actor', actor], check=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--max_bytes', type=int, default=5000)
    p.add_argument('--mark', action='store_true')
    p.add_argument('--actor', default='AI')
    args = p.parse_args()
    if not MANIFEST.exists():
        raise SystemExit('manifest missing; run scripts/generate_doc_manifest.py')
    unread = print_unread(args.max_bytes)
    if not unread:
        print('No unread files')
        return
    if args.mark:
        for path in unread:
            print('Marking read:', path)
            mark_read(path, args.actor)
        print('Marked all unread as read')


if __name__ == '__main__':
    main()
