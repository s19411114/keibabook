#!/usr/bin/env python3
"""
Find similar/duplicate markdown files under docs/ and issues/ and report pairs above a threshold.

Usage:
  python3 scripts/find_similar_docs.py --min 0.6

This outputs file pairs with SequenceMatcher ratio >= min
"""
from pathlib import Path
from difflib import SequenceMatcher
import argparse
import sys


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding='utf-8')
    except Exception:
        return ''


def score(a: str, b: str) -> float:
    # Normalize: lower + remove multiple spaces
    a2 = ' '.join(a.lower().split())
    b2 = ' '.join(b.lower().split())
    return SequenceMatcher(None, a2, b2).ratio()


def scan(base: Path, patterns=('docs', 'issues')):
    files = []
    for p in base.iterdir():
        if p.name in patterns:
            for f in p.rglob('*.md'):
                files.append(f)
    return files


def main(min_ratio: float = 0.6):
    base = Path('.')
    files = scan(base)
    if not files:
        print('No markdown files to scan')
        return 0

    contents = {f: read_text(f) for f in files}

    similar_pairs = []
    files_list = list(contents.keys())
    n = len(files_list)
    for i in range(n):
        for j in range(i+1, n):
            fa = files_list[i]
            fb = files_list[j]
            if not contents[fa] or not contents[fb]:
                continue
            r = score(contents[fa], contents[fb])
            if r >= min_ratio:
                similar_pairs.append((r, fa, fb))

    if not similar_pairs:
        print('No similar docs found')
        return 0

    similar_pairs.sort(reverse=True, key=lambda x: x[0])
    print('Similar document pairs (ratio >= {:.2f}):'.format(min_ratio))
    for r, fa, fb in similar_pairs:
        print(f'{r:.2f} : {fa} <-> {fb}')

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--min', type=float, default=0.6, help='Minimum similarity ratio (0-1)')
    args = parser.parse_args()
    sys.exit(main(args.min))
