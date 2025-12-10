#!/usr/bin/env python3
"""
generate_doc_manifest.py
Scan the repo for documentation and relevant files, generating a manifest that tracks read/unread status.

Usage: python scripts/generate_doc_manifest.py
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime

ROOT = Path('.')
MANIFEST_PATH = Path('migration/DOC_MANIFEST.json')

INCLUDE_EXTENSIONS = ['.md', '.mdown', '.txt', '.yaml', '.yml', '.py']
EXCLUDE_DIRS = ['.venv', '.git', '__pycache__', 'node_modules']


def sha1_of_file(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def is_included(path: Path) -> bool:
    if any(p in path.parts for p in EXCLUDE_DIRS):
        return False
    return path.suffix.lower() in INCLUDE_EXTENSIONS or 'docs' in path.parts or path.match('migration/**')


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        try:
            return json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}


def save_manifest(manifest: dict):
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')


def scan_and_update():
    manifest = load_manifest()
    entries = manifest.get('files', {})
    scanned = {}
    for p in sorted(ROOT.rglob('*')):
        if p.is_file() and is_included(p):
            try:
                stat = p.stat()
                sha1 = sha1_of_file(p)
                k = str(p)
                prev = entries.get(k, {})
                read = prev.get('read', False)
                # If file changed (sha1 differs) reset read flag
                if prev and prev.get('sha1') != sha1:
                    read = False
                scanned[k] = {
                    'path': k,
                    'size': stat.st_size,
                    'sha1': sha1,
                    'mtime': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'read': read,
                    'tags': [],
                }
            except Exception:
                pass
    # Mark removed files
    manifest = {
        'generated': datetime.now().isoformat(),
        'files': scanned,
    }
    save_manifest(manifest)
    print(f'Wrote {MANIFEST_PATH} ({len(scanned)} files)')


def main():
    scan_and_update()


if __name__ == '__main__':
    main()
