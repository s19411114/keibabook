#!/usr/bin/env bash
set -euo pipefail

# Simple script to create and bootstrap a .venv in the repo root.
# Usage: ./scripts/ensure_venv.sh

WORKDIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$WORKDIR"

if [ -d ".venv" ]; then
  echo ".venv already exists"
  exit 0
fi

# Use system python to create venv
PY=python3
if ! command -v $PY >/dev/null 2>&1; then
  PY=python
fi

if ! $PY -V >/dev/null 2>&1; then
  echo "Python not found in PATH"
  exit 2
fi

$PY -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
if [ -f requirements.txt ]; then
  python -m pip install -r requirements.txt
fi

echo "Created .venv and installed dependencies. Activate it with: source .venv/bin/activate"
