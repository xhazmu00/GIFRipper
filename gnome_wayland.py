"""GNOME Shell's native D-Bus screencaster as a Wayland recording backend.

The same D-Bus connection must issue both Screencast and StopScreencast.
D-Bus calls run in a dedicated asyncio event-loop thread and never on Qt's
main thread. This backend uses GNOME Shell, not Qt screen grabbing; it is not
available on KDE or wlroots compositors.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
import subprocess
import threading
import time

from recorder import RecorderError, ffmpeg_binary, no_console


BUS_NAME = 'org.gnome.Shell.Screencast'
OBJECT_PATH = '/org/gnome/Shell/Screencast'
INTERFACE = 'org.gnome.Shell.Screencast'


def is_gnome_wayland(env=None):
    env = os.environ if env is None else env
    desktop = (env.get('XDG_CURRENT_DESKTOP', '') + ':' + env.get('DESKTOP_SESSION', '')).lower()
    return env.get('XDG_SESSION_TYPE', '').lower() == 'wayland' and 'gnome' in desktop


def detect_backend(env=None):
    env = os.environ if env is None else env
    forced = env.get('GIFRIPPER_WAYLAND_BACKEND', '').lower()
    return (is_gnome_wayland(env) and forced != 'qt')


def _gif_from_video(video: Path, gif_path: str, fps: int):
    video = Path(video)
    if not video.is_file() or video.stat().st_size < 100:
        raise RecorderError('GNOME neuložilo žádné video. Záznam byl prázdný nebo jej systém odmítl.')
    target = Path(gif_path).expanduser().resolve()
    if target.suffix.lower() != '.gif':
        raise RecorderError('Cílový soubor musí být GIF (.gif).')
    target.parent.mkdir(parents=True, exist_ok=True)
    flt = (f'[0:v]fps={fps},split[a][b];[a]palettegen=stats_mode=diff[p];'
           '[b][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle[v]')
    command = [ffmpeg_binary(), '-hide_banner', '-loglevel', 'error', '-y',
               '-i', str(video), '-filter_complex', flt, '-map', '[v]',
               '-loop', '0', str(target)]
    try:
        proc = subprocess.run(command, text=True, capture_output=True, timeout=180,
                              **no_console())
    except subprocess.TimeoutExpired as exc:
        target.unlink(missing_ok=True)
        raise RecorderError('Převod záznamu na GIF překročil 180 sekund.') from exc
    if proc.returncode or not target.is_file() or target.stat().st_size == 0:
        target.unlink(missing_ok=True)
        raise RecorderError('Export GIFu selhal: ' + (proc.stderr[-1100:] or 'neznámá chyba'))
    return str(target)


class GnomeWaylandRecorder:
    """Async D-Bus GNOME Shell recording, with an owned live bus connection."""

    def __init__(self, directory: str, fps: int = 12):
        self.directory = Path(directory)
        self.fps = max(1, min(30, int(fps)))
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop,
                                       name='gifripper-gnome-dbus', daemon=True)
        self.thread.start()
        self.bus = None
        self.interface = None
        self.file: Path | None = None
        self._active = False
        self._started = 0.0

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        self.loop.close()

    def _call(self, coro, timeout: int = 15):
        task = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            return task.result(timeout=timeout)
        except Exception:
            task.cancel()
            raise

    async def _record(self):
        try:
            from dbus_next.aio import MessageBus
            from dbus_next import Variant
        except ImportError as exc:
            raise RecorderError('Chybí dbus-next. Ve složce aplikace spusť: .venv/bin/pip install dbus-next') from exc
        bus = await MessageBus().connect()
        try:
            introspect = await bus.introspect(BUS_NAME, OBJECT_PATH)
            proxy = bus.get_proxy_object(BUS_NAME, OBJECT_PATH, introspect)
            interface = proxy.get_interface(INTERFACE)
            self.bus = bus
            self.interface = interface
            template = str((self.directory / 'gnome-capture.webm').resolve())
            success, filename = await interface.call_screencast(template, {
                'framerate': Variant('i', self.fps),
                'draw-cursor': Variant('b', True),
            })
            if not success:
                raise RecorderError('GNOME Shell odmítlo spuštění záznamu. Může být obsazený rekordér nebo vypnutý ScreenCast.')
            filename = str(filename or template)
            self.file = Path(filename)
            self._active = True
            self._started = time.monotonic()
            return str(self.file)
        except Exception:
            self.interface = None
            self.bus = None
            bus.disconnect()
            raise

    def start(self):
        try:
            return self._call(self._record(), timeout=16)
        except Exception as exc:
            raise RecorderError('GNOME ScreenCast se nepodařilo spustit: ' + str(exc)) from exc

    async def _stop(self):
        if not self.interface:
            return False
        try:
            result = await self.interface.call_stop_screencast()
            self._active = False
            return bool(result if isinstance(result, bool) else result[0])
        finally:
            if self.bus:
                self.bus.disconnect()
            self.bus = None
            self.interface = None

    def stop(self, destination: str):
        if not self._active or not self.file:
            raise RecorderError('GNOME nahrávání nebylo spuštěno.')
        video = self.file
        elapsed = max(0., time.monotonic() - self._started)
        try:
            self._call(self._stop(), timeout=18)
            # GNOME encoder may need a moment to finish writing after Stop.
            deadline = time.monotonic() + 6
            while time.monotonic() < deadline:
                if video.is_file() and video.stat().st_size > 100:
                    break
                time.sleep(.16)
            output = _gif_from_video(video, destination, self.fps) if destination else ''
            return output, max(1, int(elapsed * self.fps)), 0
        finally:
            self.close()

    def close(self):
        if self._active:
            try:
                self._call(self._stop(), timeout=4)
            except Exception:
                pass
            self._active = False
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)

    @property
    def elapsed_seconds(self):
        return max(0.0, time.monotonic()-self._started) if self._active else 0.0

    @property
    def active(self):
        return self._active
