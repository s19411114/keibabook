#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
MEM_MB=${MEM_MB:-4096}
# Run the run_scraper entrypoint with a memory limit (default 4096MB)
exec python3 "$SCRIPT_DIR/run_with_mem_limit.py" --mem-mb "$MEM_MB" -- python3 "$SCRIPT_DIR/run_scraper.py" "$@"
