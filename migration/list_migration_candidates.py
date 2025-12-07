#!/usr/bin/env python3
"""List migration candidates and group them by keywords.

Usage: python migration/list_migration_candidates.py
Generates: migration/to_keiba_ai/candidates_report.md
"""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parents[0] / 'to_keiba_ai' / 'candidates_report.md'

KEYWORDS = {
    'netkeiba': ['netkeiba', 'db.netkeiba.com', 'race.netkeiba.com'],
    'pedigree': ['pedigree', 'run_pedigree', 'pedigree_queue', 'pedigree_store'],
    'track_bias': ['track_bias', 'TrackBiasAnalyzer', 'get_latest_bias'],
    'schedule': ['calendar', 'NetkeibaCalendarFetcher', 'Netkeiba calendar'],
    'odds': ['odds_fetcher', 'jra_odds', 'cli_minimal_odds'],
}

# walk files
candidates = {k: set() for k in KEYWORDS}
other = set()

ignore_dirs = {'.git', '.venv', '__pycache__', 'migration/to_keiba_ai'}

for root, dirs, files in os.walk(ROOT):
    # prune
    dirs[:] = [d for d in dirs if d not in ignore_dirs]
    for f in files:
        if f.endswith(('.py', '.md', '.json')):
            p = Path(root) / f
            try:
                txt = p.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            matched = False
            for k, kws in KEYWORDS.items():
                for kw in kws:
                    if re.search(rf"\b{re.escape(kw)}\b", txt, flags=re.I):
                        candidates[k].add(str(p.relative_to(ROOT)))
                        matched = True
                        break
                if matched:
                    break
            if not matched:
                # small heuristic: filenames containing keywords
                for k, kws in KEYWORDS.items():
                    for kw in kws:
                        if kw.lower() in f.lower():
                            candidates[k].add(str(p.relative_to(ROOT)))
                            matched = True
                            break
                    if matched: break
            if not matched:
                # track some files that mention keibabook or netkeiba in content but not matched above
                if re.search(r'netkeiba|pedigree|track_bias|pedigree_queue|run_pedigree', txt, flags=re.I):
                    other.add(str(p.relative_to(ROOT)))

# write output
lines = ["# Migration Candidates Report\n\n"]
for k, files in candidates.items():
    lines.append(f"## {k}\n")
    if not files:
        lines.append("(none)\n\n")
        continue
    for f in sorted(files):
        lines.append(f"- {f}\n")
    lines.append("\n")

if other:
    lines.append("## other (mention keywords)\n")
    for f in sorted(other):
        lines.append(f"- {f}\n")

OUT.write_text(''.join(lines), encoding='utf-8')
print(f'Wrote {OUT}')
