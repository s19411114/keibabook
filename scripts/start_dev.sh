#!/usr/bin/env bash
# Usage: scripts/start_dev.sh [--no-build] [--open]
# This script is intended to be run from WSL or Linux/Mac, and automates:
# 1) Syncing workspace from /mnt/c (if needed)
# 2) Starting docker compose with the project mounted
# 3) Starting Streamlit in the app container

set -euo pipefail

OPEN_BROWSER=false
BUILD=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-build) BUILD=false; shift ;;
    --open) OPEN_BROWSER=true; shift ;;
    *) shift ;;
  esac
done

# If running from WSL and there's a host path, keep it in sync
if [[ -d "/mnt/c/GeminiCLI/TEST/keibabook" && -d "$HOME" ]]; then
  echo "Syncing files to WSL home for better I/O performance..."
  rsync -a --delete /mnt/c/GeminiCLI/TEST/keibabook/ $HOME/keibabook/
  HOST_DIR="$HOME/keibabook"
else
  HOST_DIR=$(pwd)
fi

cd $HOST_DIR

export HOST_PROJECT_DIR=$HOST_DIR

if $BUILD ; then
  echo "Building and starting containers..."
  docker compose up -d --build
else
  echo "Starting containers..."
  docker compose up -d
fi

echo "Starting Streamlit in container..."
docker compose exec -T app bash -lc 'streamlit run app.py --server.port=8501' &

if $OPEN_BROWSER ; then
  if which xdg-open >/dev/null 2>&1; then
    xdg-open http://localhost:8501
  elif which open >/dev/null 2>&1; then
    open http://localhost:8501
  fi
fi

echo "App started at http://localhost:8501"
