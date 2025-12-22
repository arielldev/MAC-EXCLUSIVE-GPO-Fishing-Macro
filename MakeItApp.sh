#!/bin/bash
set -e
cd "$(dirname "$0")"

# Activate venv if exists
if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

# Ensure pyinstaller is available
if ! python3 -c "import PyInstaller" >/dev/null 2>&1; then
  pip install pyinstaller
fi

echo "Building macOS app bundle..."
pyinstaller \
  --noconfirm \
  --windowed \
  --name "GPO Autofish" \
  --add-data "images:images" \
  --add-data "presets:presets" \
  --add-data "default_settings.json:." \
  --add-data "layout_settings.json:." \
  src/main.py

echo "✅ Build complete. See 'dist/GPO Autofish.app'"
