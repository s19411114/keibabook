#!/usr/bin/env python3
"""
Extract completed (DONE/closed/resolved) section from docs/ISSUES_MASTER.md
and archive them into docs/archived/; append a short entry into PROJECT_LOG.md.

Usage:
  python scripts/extract_completed_from_issues_master.py --dry-run
  python scripts/extract_completed_from_issues_master.py --confirm
"""
import argparse
from datetime import datetime
from pathlib import Path
import re
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ISSUES_MASTER = PROJECT_ROOT / 'docs' / 'ISSUES_MASTER.md'
ARCHIVE_DIR = PROJECT_ROOT / 'docs' / 'archived' / 'issues_master'
CONSOLIDATED_ARCHIVE = PROJECT_ROOT / 'docs' / 'archived' / 'completed_issues.md'
PROJECT_LOG = PROJECT_ROOT / 'PROJECT_LOG.md'


def slugify_header(header: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_-]', '_', header.strip())[:80]


def parse_sections(md_text: str):
    # split on header lines that start with '#### '
    parts = re.split(r'(?m)^(####\s+)', md_text)
    # parts alternates between preamble, '#### ' and content
    if len(parts) < 2:
        return []
    sections = []
    # Reconstruct sequences
    i = 0
    preamble = parts[0]
    i = 1
    while i < len(parts):
        header_prefix = parts[i]  # '#### '
        content_block = parts[i + 1] if i + 1 < len(parts) else ''
        # Now header/content: header line is the first line of content_block
        header_line, *rest = content_block.splitlines(True)
        header_full = (header_prefix + header_line).strip()
        body = ''.join(rest)
        sections.append({'header': header_full, 'body': body, 'raw': header_full + '\n' + body})
        i += 2
    return preamble, sections


def detect_done_status(section_body: str) -> bool:
    # Find a '- status:' field in the section body (case-insensitive)
    m = re.search(r'(?mi)^\s*-\s*status\s*:\s*(\S+)', section_body)
    if m:
        status = m.group(1).strip().lower()
        return status in ('done', 'closed', 'resolved', 'archived')
    return False


def archive_section(section, dest_dir: Path, dry_run: bool = True, consolidate: bool = True):
    ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    header = section['header'].replace('####', '').strip()
    slug = slugify_header(header).lower() or 'issue'
    dest_dir.mkdir(parents=True, exist_ok=True)
    if consolidate:
        # Append to a single consolidated archive file
        dest = CONSOLIDATED_ARCHIVE
        if dry_run:
            print(f"[DRY-RUN] Would append section '{header}' to consolidated archive -> {dest}")
            return dest
        with open(dest, 'a', encoding='utf-8') as f:
            f.write(f"\n#### {header}\n")
            f.write(section['body'])
            f.write(f"\nArchivedAt: {ts}Z\n")
    else:
        dest_name = f"archived-{ts}-{slug}.md"
        dest = dest_dir / dest_name
        if dry_run:
            print(f"[DRY-RUN] Would archive section '{header}' -> {dest}")
            return dest
        with open(dest, 'w', encoding='utf-8') as f:
            f.write(section['raw'])
            f.write(f"\nArchivedAt: {ts}Z\n")
    # append to PROJECT_LOG.md
    if PROJECT_LOG.exists():
        with open(PROJECT_LOG, 'a', encoding='utf-8') as pl:
            pl.write(f"\n- Archived issue '{header}' -> {dest.name} at {ts}Z\n")
    else:
        with open(PROJECT_LOG, 'w', encoding='utf-8') as pl:
            pl.write(f"# Project Log\n\n- Archived issue '{header}' -> {dest.name} at {ts}Z\n")
    print(f"Archived '{header}' -> {dest}")
    return dest


def run(dry_run=True, consolidate=True, output_json_path: str = None):
    if not ISSUES_MASTER.exists():
        print('ISSUES_MASTER.md not found')
        return 1
    text = ISSUES_MASTER.read_text(encoding='utf-8')
    preamble, sections = parse_sections(text)
    if not sections:
        print('No sections detected in ISSUES_MASTER.md')
        return 0
    keep_sections = []
    archived = []
    for sec in sections:
        if detect_done_status(sec['body']):
            archived.append(sec)
        else:
            keep_sections.append(sec)
    if not archived:
        print('No completed sections to archive.')
        return 0
    print(f"Detected {len(archived)} completed sections to archive.")
    for sec in archived:
        archive_section(sec, ARCHIVE_DIR, dry_run=dry_run, consolidate=consolidate)

    # Optionally write out a JSON list of detected sections for CI to parse
    if output_json_path:
        try:
            import json as _json
            data = [ {'header': s['header'].replace('####','').strip(), 'slug': slugify_header(s['header']) } for s in archived ]
            with open(output_json_path, 'w', encoding='utf-8') as oj:
                _json.dump(data, oj, ensure_ascii=False, indent=2)
            print(f"Wrote detection JSON: {output_json_path}")
        except Exception as e:
            print(f"Warning: failed to write output json: {e}")
    if dry_run:
        print('\nDry-run complete. No changes made to ISSUES_MASTER.md')
        return 0
    # write back remaining sections
    with open(ISSUES_MASTER, 'w', encoding='utf-8') as f:
        f.write(preamble)
        for sec in keep_sections:
            f.write(sec['raw'])
    print(f"Removed {len(archived)} sections from {ISSUES_MASTER} and archived to {ARCHIVE_DIR}")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--confirm', action='store_true', help='Execute archive (not dry-run)')
    parser.add_argument('--separate', action='store_true', help='Archive sections as separate files instead of consolidating')
    parser.add_argument('--output-json', help='Write detected candidate list to JSON (for CI)')
    args = parser.parse_args()
    consolidate = not args.separate
    return run(dry_run=not args.confirm, consolidate=consolidate, output_json_path=args.output_json)


if __name__ == '__main__':
    main()
