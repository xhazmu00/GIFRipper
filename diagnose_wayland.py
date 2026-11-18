#!/usr/bin/env python3
"""GNOME Wayland ScreenCast diagnostics. No screenshot without --record."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from gnome_wayland import GnomeWaylandRecorder, detect_backend


def main():
    parser = argparse.ArgumentParser(description='GIFRipper 2.3 GNOME Wayland diagnostic')
    parser.add_argument('--record', action='store_true',
                        help='Record a 3-second full-screen GIF (sensitive screen contents!)')
    parser.add_argument('--out', default='wayland-test.gif', help='Output GIF used with --record')
    args = parser.parse_args()
    for key in ('XDG_SESSION_TYPE', 'XDG_CURRENT_DESKTOP', 'DESKTOP_SESSION',
                'WAYLAND_DISPLAY', 'DBUS_SESSION_BUS_ADDRESS'):
        value = os.environ.get(key, '<nenastaveno>')
        # Do not expose the contents of the session bus address in logs.
        if key == 'DBUS_SESSION_BUS_ADDRESS':
            value = '<nastaveno>' if key in os.environ else '<nenastaveno>'
        print(f'{key}: {value}', flush=True)
    print('GNOME backend zvolen:', detect_backend(), flush=True)
    for binary in ('gdbus', 'ffmpeg'):
        print(binary + ':', shutil.which(binary) or 'CHYBÍ', flush=True)
    if shutil.which('gdbus'):
        cmd = ['gdbus', 'introspect', '--session',
               '--dest', 'org.gnome.Shell.Screencast',
               '--object-path', '/org/gnome/Shell/Screencast']
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            print('Screencast D-Bus dostupné:',
                  result.returncode == 0 and 'Screencast(' in result.stdout,
                  flush=True)
            if result.returncode:
                print('D-Bus odpověď:', (result.stderr or result.stdout).strip()[-800:], flush=True)
        except Exception as exc:
            print('D-Bus chyba:', type(exc).__name__, str(exc)[:200], flush=True)
    if not args.record:
        print('Pouze diagnostika; nahrávání nebylo spuštěno.')
        print('Pro test videa použij: .venv/bin/python diagnose_wayland.py --record')
        return 0
    if not detect_backend():
        print('Tento test vyžaduje GNOME + Wayland (bez vynuceného Qt backendu).')
        return 2
    if not shutil.which('ffmpeg'):
        print('Chybí ffmpeg. Ubuntu: sudo apt install ffmpeg')
        return 2
    # Explicitly opted-in: screen contents will be captured.
    with tempfile.TemporaryDirectory(prefix='gifripper-wayland-test-') as temp:
        recorder = GnomeWaylandRecorder(temp, fps=8)
        try:
            for i in (3, 2, 1):
                print('Nahrávání začne za:', i, flush=True)
                time.sleep(1)
            print('Spouštím nativní GNOME ScreenCast…', flush=True)
            video = recorder.start()
            print('Záznam běží:', video, flush=True)
            time.sleep(3)
            output, frames, _ = recorder.stop(str(Path(args.out).resolve()))
            print('HOTOVO: ', output, 'snímků (odhad):', frames, flush=True)
            return 0
        except Exception as exc:
            print('CHYBA:', str(exc), flush=True)
            return 1
        finally:
            recorder.close()


if __name__ == '__main__':
    raise SystemExit(main())
