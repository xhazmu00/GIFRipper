#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
if ! command -v python3 >/dev/null; then
  echo 'Missing Python 3 (3.11+ is recommended).' >&2
  exit 1
fi
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
if ! .venv/bin/python -c 'import PySide6.QtMultimedia, PIL, dbus_next' >/dev/null 2>&1; then
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -r requirements.txt
fi
if ! command -v ffmpeg >/dev/null && [ ! -x bin/ffmpeg ]; then
  echo 'WARNING: FFmpeg is missing. On Ubuntu: sudo apt install ffmpeg' >&2
fi
exec .venv/bin/python app.py "$@"
