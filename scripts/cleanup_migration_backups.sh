#!/usr/bin/env bash
set -euo pipefail
# Archive any .bak files in migration/backups and remove them
BASEDIR=$(dirname "$0")/.. 
BACKUP_DIR="$BASEDIR/migration/backups"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
ARCHIVE="$BACKUP_DIR/backup_removed_${TIMESTAMP}.tar.gz"

echo "Archiving .bak files in $BACKUP_DIR"
shopt -s nullglob
BAK_FILES=($BACKUP_DIR/*.bak)
if [ ${#BAK_FILES[@]} -eq 0 ]; then
    echo "No .bak files found in $BACKUP_DIR"
    exit 0
fi
tar -czvf "$ARCHIVE" "${BAK_FILES[@]}"
echo "Archived to $ARCHIVE"
# remove originals
rm -f "${BAK_FILES[@]}"
echo "Removed: ${#BAK_FILES[@]} .bak files"

echo "Done"
