#!/usr/bin/env bash
# Small helper script to copy the project into WSL home and start docker-compose
# Usage: ./scripts/docker-start-wsl.sh [wsl-username]

set -euo pipefail

WSL_USER=${1:-$(whoami)}
WSL_HOME="/home/${WSL_USER}"
DEST_DIR="${WSL_HOME}/keibabook"
SRC_DIR="/mnt/c/GeminiCLI/TEST/keibabook"

echo "Copying project to WSL home: ${DEST_DIR}"
rm -rf "${DEST_DIR}" || true
cp -r "${SRC_DIR}" "${DEST_DIR}"

cd "${DEST_DIR}"
echo "Starting docker-compose with HOST_PROJECT_DIR=${DEST_DIR}"
HOST_PROJECT_DIR="${DEST_DIR}" docker-compose up --build
