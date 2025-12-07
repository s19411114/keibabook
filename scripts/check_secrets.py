#!/usr/bin/env python3
"""
Lightweight secret scanner to detect accidental credentials in the repo.
Usage: python scripts/check_secrets.py --path .
Exits with code 1 if suspicious secrets are found.
"""
import argparse
import os
import re
from pathlib import Path

DEFAULT_IGNORE_DIRS = [".git", "docs/archived", "vendor", "venv", ".venv", "__pycache__"]

PATTERNS = [
    re.compile(r"\bLOGIN_ID\s*=\s*\S+", re.I),
    re.compile(r"\bLOGIN_PASSWORD\s*=\s*\S+", re.I),
    re.compile(r"\bLOGIN_ID\b:.*\S+", re.I),
    re.compile(r"\bLOGIN_PASSWORD\b:.*\S+", re.I),
    re.compile(r"password\s*[:=]\s*\".+\"", re.I),
    re.compile(r"password\s*[:=]\s*'[^']+" , re.I),
    re.compile(r"password\s*[:=]\s*[^\s#]+", re.I),
    re.compile(r"aws_access_key_id\s*=\s*\S+", re.I),
    re.compile(r"aws_secret_access_key\s*=\s*\S+", re.I),
]

EXCLUDE_FILE_PATTERNS = ["*.md", "docs/*", "tests/*", "docs/archived/*"]


def find_files(root: Path):
    for p in root.rglob("*"):
        # ignore files under ignored directories
        if any(part in DEFAULT_IGNORE_DIRS for part in p.parts):
            continue
        if any(p.match(pat) for pat in EXCLUDE_FILE_PATTERNS):
            continue
        yield p


def scan_file(p: Path):
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        return []
    findings = []
    for pattern in PATTERNS:
        for m in pattern.finditer(text):
            snippet = m.group(0).strip()
            if ":" in snippet or "=" in snippet:
                val = snippet.split("=", 1)[1] if "=" in snippet else snippet.split(":", 1)[1]
                if not val or val.strip() in ["\"\"", "''", "", '"', "''"]:
                    continue
            findings.append((p, pattern.pattern, snippet))
    return findings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default='.', help='Path to scan')
    parser.add_argument("--fail-if-any", action='store_true', help='Exit with code 1 if any findings')
    args = parser.parse_args()

    root = Path(args.path).resolve()
    all_findings = []
    for p in find_files(root):
        if p.suffix in ['.png', '.jpg', '.jpeg', '.gif', '.gz', '.zip']:
            continue
        res = scan_file(p)
        if res:
            all_findings.extend(res)

    if not all_findings:
        print("No suspicious credentials found.")
        return 0

    print("Potential credential-like patterns detected (please review):")
    for p, pat, snippet in all_findings:
        print(f"- {p} | {pat} | {snippet[:200]}")

    if args.fail_if_any:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
