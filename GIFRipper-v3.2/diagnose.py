"""Report screen-capture prerequisites without starting the GUI."""
import os
import platform
import shutil
import subprocess
from importlib.metadata import version, PackageNotFoundError

print('GIFRipper diagnostic')
print('OS:', platform.platform())
print('Python:', platform.python_version())
for name in ('PySide6', 'Pillow'):
    try: print(name+':',version(name))
    except PackageNotFoundError: print(name+': MISSING')
print('DISPLAY:',os.getenv('DISPLAY','(unset)'))
print('WAYLAND_DISPLAY:',os.getenv('WAYLAND_DISPLAY','(unset)'))
print('XDG_SESSION_TYPE:',os.getenv('XDG_SESSION_TYPE','(unset)'))
print('QT_QPA_PLATFORM:',os.getenv('QT_QPA_PLATFORM','(unset)'))
print('FFmpeg:',shutil.which('ffmpeg') or 'MISSING')
if platform.system()=='Linux':
    for name in ('xdg-desktop-portal', 'pipewire', 'wireplumber'):
        result=subprocess.run(['pgrep','-a','-f',fr'(^|/){name}( |$|-)'],capture_output=True,text=True,timeout=5)
        print(name, 'RUNNING' if result.returncode==0 else 'not detected')

# Check whether the PySide6 wheel ships a native Wayland QPA plugin.
try:
    from PySide6.QtCore import QLibraryInfo
    from pathlib import Path
    platforms = Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)) / 'platforms'
    plugins = sorted(p.name for p in platforms.glob('*wayland*'))
    print('Qt Wayland plugins:', ', '.join(plugins) if plugins else 'NONE FOUND')
except ImportError as exc:
    print('Qt plugin diagnosis unavailable:', exc)
except Exception as exc:
    print('Qt plugin diagnosis failed:', exc)

if platform.system() == 'Linux':
    mode = (os.environ.get('XDG_SESSION_TYPE') or 'unknown').lower()
    print('Recommended backend:', 'Qt + Wayland ScreenCast portal' if mode == 'wayland' else
          'FFmpeg x11grab' if os.environ.get('DISPLAY') else 'No desktop session detected')
    if mode == 'wayland':
        print('Wayland hint: first approve the OS screen-sharing picker.')
        print('If portal/Qt keeps failing: try an Ubuntu on Xorg login session.')
