#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
MEM_MB=${MEM_MB:-2048}
exec python3 "$SCRIPT_DIR/run_with_mem_limit.py" --mem-mb "$MEM_MB" -- .venv/bin/python app_nicegui.py
