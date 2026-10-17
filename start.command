#!/bin/bash
# macOS: double-click to start SnapSolve (first run sets itself up; needs python3 from python.org or Homebrew).
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv && source .venv/bin/activate && python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt || { echo "Setup failed."; read -p "Press Enter to close"; exit 1; }
else
  source .venv/bin/activate
fi
nohup python -m app.main >/dev/null 2>&1 &
disown
exit
