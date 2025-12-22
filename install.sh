#!/bin/bash
set -e

echo "========================================"
echo "  GPO Autofish - Easy Installation (macOS)"
echo "========================================"
echo

# 1) Check Python installation
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is not installed or not in PATH"
  echo "Install via Homebrew: brew install python@3.13 (recommended)"
  echo "Or download from https://python.org"
  exit 1
fi

PY_VER=$(python3 -c 'import sys; print("%d.%d"%sys.version_info[:2])')
echo "✓ Python ${PY_VER} found"

MAJOR=${PY_VER%%.*}
MINOR=${PY_VER#*.}
if [ "$MAJOR" -ne 3 ] || { [ "$MINOR" -ne 12 ] && [ "$MINOR" -ne 13 ]; }; then
  echo "WARNING: Use Python 3.12 or 3.13 for best compatibility"
fi

# 2) Create virtual environment
if [ ! -d ".venv" ]; then
  echo
  echo "[1/3] Creating virtual environment..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

# 3) Upgrade pip and install packages
echo
echo "[2/3] Upgrading pip..."
pip install --upgrade pip >/dev/null || true

echo
echo "[3/3] Installing required packages (this can take a while)..."
PACKAGES=(
  pillow
  mss
  numpy
  opencv-python
  easyocr
  pynput
  requests
)

for pkg in "${PACKAGES[@]}"; do
  echo "Installing ${pkg}..."
  pip install "$pkg" >/dev/null || {
    echo "✗ ${pkg} failed to install"
  }
  echo "✓ ${pkg}"
done

echo
echo "Optional: Install Tesseract OCR via Homebrew if needed"
echo "  brew install tesseract"

echo
python3 - <<'PY'
try:
  import PIL, mss, numpy, cv2, easyocr, pynput, requests
  print('✓ Core modules verified')
except Exception as e:
  print('WARNING: Some modules failed to import:', e)
PY

echo
echo "========================================"
echo "  Installation Complete!"
echo "========================================"
echo
echo "Run:"
echo "  • ./run.sh    (silent/background)"
echo "  • ./run_dev.sh (with console)"
