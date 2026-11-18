"""Build an executable ON THE TARGET OPERATING SYSTEM with PyInstaller.

Windows -> dist/GIFRipper/GIFRipper.exe
macOS   -> dist/GIFRipper.app
Linux   -> dist/GIFRipper/GIFRipper

`pip install pyinstaller` before running. Bundle your licensed FFmpeg binary
under bin/ if you want truly offline distribution; otherwise use system FFmpeg.
"""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
icon = root / 'assets' / ('icon.ico' if sys.platform == 'win32' else 'icon.icns' if sys.platform == 'darwin' else 'icon.png')
add_data = 'assets' + (';' if sys.platform == 'win32' else ':') + 'assets'
cmd = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
       '--name', 'GIFRipper', '--windowed', '--icon', str(icon),
       '--add-data', add_data, '--collect-all', 'PySide6.QtMultimedia',
       str(root/'app.py')]
if (root/'bin').exists():
    cmd.extend(['--add-data', 'bin'+(';' if sys.platform=='win32' else ':')+'bin'])
print(' '.join(cmd))
subprocess.run(cmd,check=True,cwd=root)
