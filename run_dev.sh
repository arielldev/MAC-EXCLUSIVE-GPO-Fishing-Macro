#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "========================================"
echo "  GPO Autofish - Development Mode (macOS)"
echo "========================================"
echo

# Prefer venv python if present
PY="python3"
if [ -x .venv/bin/python ]; then
  PY="./.venv/bin/python"
  echo "✓ Using venv Python: ${PY}"
else
  echo "⚠️ Virtual environment not found - using system Python"
fi

echo "Starting with console output..."
"$PY" src/main.py
