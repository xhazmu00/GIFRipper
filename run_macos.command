#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
if ! .venv/bin/python -c 'import PySide6.QtMultimedia, PIL' 2>/dev/null; then
  .venv/bin/python -m pip install -r requirements.txt
fi
if ! command -v ffmpeg >/dev/null; then
  echo 'FFmpeg missing: brew install ffmpeg'
fi
exec .venv/bin/python app.py "$@"
