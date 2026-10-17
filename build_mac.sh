#!/bin/bash
# macOS: builds dist/SnapSolve.app (no installer, no admin password).
set -e
cd "$(dirname "$0")"
python3 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python tools/make_icon.py
python -m PyInstaller --noconfirm --clean --windowed --name SnapSolve --icon assets/icon.icns \
  --osx-bundle-identifier com.snapsolve.app --paths . --add-data "assets:assets" \
  --collect-all rapidocr_onnxruntime --collect-data wordninja \
  --hidden-import pynput.keyboard._darwin --hidden-import pynput.mouse._darwin app/main.py
codesign --force --deep --sign - dist/SnapSolve.app || true   # ad-hoc signature (required on Apple Silicon)
echo "Done: dist/SnapSolve.app"
