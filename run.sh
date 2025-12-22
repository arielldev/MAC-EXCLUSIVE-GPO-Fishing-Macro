#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "========================================"
echo "  GPO Autofish - Starting (macOS)"
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

echo "Starting in background (silent)..."
nohup "$PY" src/main.py >/dev/null 2>&1 &
PID=$!
echo "✅ Macro started (PID: $PID)."
echo "Use 'kill $PID' to stop."
