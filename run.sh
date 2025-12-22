#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "========================================"
echo "  GPO Autofish - Starting (macOS)"
echo "========================================"
echo

# Activate venv if exists
if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
  echo "✓ Virtual environment activated"
else
  echo "⚠️ Virtual environment not found - using system Python"
fi

echo "Starting in background (silent)..."
nohup python3 src/main.py >/dev/null 2>&1 &
PID=$!
echo "✅ Macro started (PID: $PID)."
echo "Use 'kill $PID' to stop."
