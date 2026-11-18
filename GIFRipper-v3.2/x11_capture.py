"""Reliable X11 capture helper for GIFRipper (no Qt multimedia dependency).

Never use this for a Wayland session: x11grab can only see XWayland
surfaces and would yield misleading/blank desktop recordings.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import threading
import time

from recorder import EncodingQueue, RecorderError, ffmpeg_binary, no_console


def is_x11_session(environment=None):
    env = os.environ if environment is None else environment
    session = env.get('XDG_SESSION_TYPE', '').lower()
    if session == 'wayland' or (session != 'x11' and env.get('WAYLAND_DISPLAY')):
        return False
    return bool(env.get('DISPLAY'))


def _capture_location(display: str, x: int, y: int) -> str:
    if not display or x < 0 or y < 0:
        raise RecorderError('Chybí X11 DISPLAY nebo je oblast mimo obrazovku.')
    # The last two plus signs are FFmpeg's display coordinate separator.
    return f'{display}+{int(x)},{int(y)}'


def capture_preview(destination: str | Path, width: int, height: int,
                    screen_x: int = 0, screen_y: int = 0,
                    display: str | None = None, timeout: int = 14) -> Path:
    """Obtain a still directly from X11 in a thread (never the GUI thread)."""
    source = _capture_location(display or os.environ.get('DISPLAY', ''), screen_x, screen_y)
    destination = Path(destination)
    cmd = [ffmpeg_binary(), '-nostdin', '-hide_banner', '-loglevel', 'error', '-y',
           '-f', 'x11grab', '-video_size', f'{width}x{height}',
           '-framerate', '1', '-i', source,
           '-frames:v', '1', '-update', '1', str(destination)]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout, **no_console())
    except subprocess.TimeoutExpired as exc:
        raise RecorderError('Čekání na snímek obrazovky X11 překročilo limit.') from exc
    if result.returncode or not destination.is_file() or destination.stat().st_size < 100:
        detail = result.stderr.decode('utf-8', errors='replace')[-900:].strip()
        raise RecorderError('Nelze získat náhled obrazovky přes X11. ' + detail)
    return destination


class X11FrameSource:
    """Read X11 frames from FFmpeg into the existing asynchronous encoder.

    Both FFmpeg pipes are consumed on background threads.  The Qt thread only
    sees monotonic statistics and short nonblocking pause/stop operations.
    """

    def __init__(self, x: int, y: int, width: int, height: int, fps: int,
                 display: str | None = None):
        if width < 80 or height < 60 or not 1 <= fps <= 30:
            raise RecorderError('Neplatná velikost oblasti nebo FPS.')
        self.x, self.y, self.width, self.height, self.fps = x, y, width, height, fps
        self.display = display or os.environ.get('DISPLAY', '')
        self.encoder: EncodingQueue | None = None
        self.source: subprocess.Popen | None = None
        self.thread: threading.Thread | None = None
        self.error: str | None = None
        self.frames_received = 0
        self.last_frame_at = 0.0
        self.stopping = threading.Event()
        self.paused = False
        self._error_buffer = bytearray()

    def start(self):
        self.encoder = EncodingQueue(self.width, self.height, self.fps)
        source = _capture_location(self.display, self.x, self.y)
        cmd = [ffmpeg_binary(), '-nostdin', '-hide_banner', '-loglevel', 'error',
               '-f', 'x11grab', '-framerate', str(self.fps),
               '-video_size', f'{self.width}x{self.height}', '-i', source,
               '-an', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-']
        try:
            self.source = subprocess.Popen(
                cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, bufsize=0, **no_console())
        except Exception:
            self.encoder.session.cleanup()
            raise
        self.thread = threading.Thread(target=self._consume, name='gifripper-x11-reader', daemon=True)
        self.thread.start()
        threading.Thread(target=self._read_errors, name='gifripper-x11-stderr', daemon=True).start()

    def _read_errors(self):
        if not self.source or not self.source.stderr:
            return
        for chunk in iter(lambda: self.source.stderr.read(1024), b''):
            self._error_buffer.extend(chunk)
            if len(self._error_buffer) > 3000:
                del self._error_buffer[:-3000]

    def _consume(self):
        assert self.source and self.source.stdout and self.encoder
        length = self.width * self.height * 4
        try:
            while not self.stopping.is_set():
                buffer = bytearray()
                while len(buffer) < length and not self.stopping.is_set():
                    data = self.source.stdout.read(length - len(buffer))
                    if not data:
                        if not self.stopping.is_set():
                            msg = self._error_buffer.decode('utf-8', 'replace').strip()
                            raise RecorderError('Zdroj obrazovky X11 skončil. ' + msg)
                        return
                    buffer.extend(data)
                if len(buffer) != length:
                    break
                self.last_frame_at = time.monotonic()
                self.frames_received += 1
                if not self.paused:
                    self.encoder.write(bytes(buffer))
        except Exception as exc:
            if not self.stopping.is_set():
                self.error = str(exc)

    def pause(self):
        self.paused = True
        if self.encoder:
            self.encoder.pause()

    def resume(self):
        if self.encoder:
            self.encoder.resume()
        self.paused = False

    def stop(self, destination: str) -> tuple[str, int, int]:
        """Blocking: call exclusively from a background thread."""
        if not self.encoder or not self.source:
            raise RecorderError('Záznam ještě nebyl zahájen.')
        self.stopping.set()
        if self.source.poll() is None:
            self.source.terminate()
            try:
                self.source.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.source.kill()
                self.source.wait(timeout=3)
        if self.thread:
            self.thread.join(timeout=4)
        if self.thread and self.thread.is_alive():
            self.encoder.session.cleanup()
            raise RecorderError('Zdroj X11 se nepodařilo korektně zastavit.')
        if self.error:
            self.encoder.session.cleanup()
            raise RecorderError(self.error)
        gif = self.encoder.finalize(destination)
        return gif, self.encoder.session.frames, self.encoder.dropped

    def cancel(self):
        self.stopping.set()
        if self.source and self.source.poll() is None:
            self.source.kill()
        if self.encoder:
            self.encoder.session.cleanup()
