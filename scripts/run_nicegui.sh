#!/usr/bin/env bash
set -euo pipefail
# Run using the venv's python to avoid sourcing PS1 in non-interactive shells
exec .venv/bin/python app_nicegui.py
