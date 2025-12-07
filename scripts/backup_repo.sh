#!/usr/bin/env bash
# Create a simple zip backup of the repo root into migration/backups
set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="$REPO_ROOT/migration/backups"
mkdir -p "$BACKUP_DIR"
TS=$(date +'%Y%m%dT%H%M%S')
OUT="$BACKUP_DIR/keibabook_backup_$TS.zip"
# Exclude venvs and large data directories
zip -r "$OUT" "$REPO_ROOT" -x "*.git/*" "*.venv/*" "*.pyc" "*data/*" "*.venv/*" 

echo "Backup created: $OUT"
chmod +x "$OUT"
