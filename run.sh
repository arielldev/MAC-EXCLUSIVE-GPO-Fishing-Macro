#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

echo "========================================"
echo "  GPO Autofish - Starting (macOS)"
echo "========================================"
echo

# Ensure Python3 is available
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found. Install via Homebrew: brew install python@3.13"
  exit 1
fi

# Create venv if missing
if [ ! -d .venv ]; then
  echo "Creating virtual environment (.venv)..."
  python3 -m venv .venv
fi

# Prefer venv python
PY="./.venv/bin/python3"
[ -x "$PY" ] || PY="./.venv/bin/python"
[ -x "$PY" ] || PY="python3"
echo "Using Python: $PY"

# Ensure dependencies are installed (quick check)
NEED_INSTALL=0
"$PY" - <<'PY' || NEED_INSTALL=1
try:
  import mss, numpy, cv2, PIL, pynput, requests
  print('deps-ok')
except Exception:
  raise SystemExit(1)
PY

if [ "$NEED_INSTALL" -eq 1 ]; then
  echo "Installing/repairing dependencies..."
  "$PY" -m pip install --upgrade pip >/dev/null 2>&1 || true
  "$PY" -m pip install pillow mss numpy opencv-python easyocr pynput requests
fi

echo "Starting in background (silent)..."
nohup "$PY" src/main.py >/dev/null 2>&1 &
PID=$!
echo "✅ Macro started (PID: $PID)."
echo "Use 'kill $PID' to stop."
