"""Cross-platform RGBA video writer and GIF encoder.

Capture pixels are provided by Qt Multimedia (Windows/macOS/X11/Wayland).
FFmpeg ONLY encodes received frames; it never accesses the screen directly.
"""
from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import time
import queue
import threading


class RecorderError(RuntimeError):
    pass


def ffmpeg_binary() -> str:
    locations = []
    if getattr(sys, 'frozen', False):
        locations.append(Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent)) / 'bin' / ('ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'))
    locations.append(Path(__file__).resolve().parent / 'bin' / ('ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'))
    for path in locations:
        if path.is_file():
            return str(path)
    found = shutil.which('ffmpeg')
    if found:
        return found
    raise RecorderError('Chybí FFmpeg. Ubuntu: sudo apt install ffmpeg | Windows: winget install Gyan.FFmpeg | macOS: brew install ffmpeg')


def no_console() -> dict:
    return {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}


class RecordingSession:
    """Feed constant-rate RGBA snapshots to ffmpeg's stdin (no X11 dependency)."""

    def __init__(self, width: int, height: int, fps: int = 12):
        if width < 80 or height < 60 or not 1 <= fps <= 30:
            raise ValueError('Oblast musí mít alespoň 80 × 60 px, FPS v rozsahu 1–30.')
        self.width, self.height, self.fps = width, height, fps
        self._temp: tempfile.TemporaryDirectory | None = None
        self.proc: subprocess.Popen | None = None
        self._log = None
        self.video_path: Path | None = None
        self.frames = 0
        self.started = 0.0
        self.paused = False
        self._pause_start = 0.0
        self._pause_total = 0.0
        self._frozen_time = 0.0

    def start(self) -> None:
        if self.proc is not None:
            raise RecorderError('Nahrávání již běží.')
        binary = ffmpeg_binary()
        self._temp = tempfile.TemporaryDirectory(prefix='gifripper-')
        self.video_path = Path(self._temp.name) / 'capture.mkv'
        self._log = open(Path(self._temp.name) / 'capture.log', 'w+', encoding='utf-8')
        cmd = [binary, '-hide_banner', '-loglevel', 'error', '-y',
               '-f', 'rawvideo', '-pixel_format', 'rgba',
               '-video_size', f'{self.width}x{self.height}',
               '-framerate', str(self.fps), '-i', '-',
               '-an', '-c:v', 'ffv1', '-level', '3', '-pix_fmt', 'bgr0',
               str(self.video_path)]
        try:
            self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                         stderr=self._log, **no_console())
        except Exception:
            self.cleanup()
            raise
        self.started = time.monotonic()

    @property
    def elapsed_seconds(self) -> float:
        if not self.started:
            return 0.0
        if self.proc is None:
            return self._frozen_time
        instant = self._pause_start if self.paused else time.monotonic()
        return max(0.0, instant - self.started - self._pause_total)

    def error(self) -> str | None:
        if self.proc and self.proc.poll() is not None:
            self._log.flush()
            self._log.seek(0)
            return self._log.read().strip() or 'FFmpeg se neočekávaně ukončil.'
        return None

    def write_rgba(self, pixels: bytes) -> None:
        if self.paused:
            return
        if not self.proc or not self.proc.stdin:
            raise RecorderError('Nahrávání není spuštěno.')
        expected = self.width * self.height * 4
        if len(pixels) != expected:
            raise RecorderError(f'Neplatná velikost snímku: {len(pixels)} místo {expected} bajtů.')
        if self.proc.poll() is not None:
            raise RecorderError(self.error() or 'Proces nahrávání skončil.')
        try:
            self.proc.stdin.write(pixels)
        except (BrokenPipeError, OSError) as exc:
            raise RecorderError(self.error() or 'Nahrávání dat selhalo.') from exc
        self.frames += 1

    def pause(self) -> None:
        if not self.paused and self.proc:
            self._pause_start = time.monotonic()
            self.paused = True

    def resume(self) -> None:
        if self.paused:
            self._pause_total += time.monotonic() - self._pause_start
            self._pause_start = 0.0
            self.paused = False

    def stop(self) -> Path:
        if not self.proc or not self.video_path:
            raise RecorderError('Není co zastavit.')
        self._frozen_time = self.elapsed_seconds
        self.paused = False
        process = self.proc
        self.proc = None
        if process.stdin:
            process.stdin.close()
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise RecorderError('FFmpeg neodpověděl a musel být ukončen.')
        if process.returncode != 0 or self.frames == 0 or not self.video_path.is_file():
            self._log.flush()
            self._log.seek(0)
            raise RecorderError(self._log.read().strip() or 'Záznam je prázdný.')
        return self.video_path

    def encode_gif(self, destination: str | os.PathLike[str]) -> Path:
        if not self.video_path or not self.video_path.is_file():
            raise RecorderError('Nahraný soubor není dostupný.')
        target = Path(destination).expanduser().resolve()
        if target.suffix.lower() != '.gif':
            raise RecorderError('Cílový soubor musí být .gif.')
        target.parent.mkdir(parents=True, exist_ok=True)
        filter_chain = (
            f'[0:v]fps={self.fps},split[a][b];'
            '[a]palettegen=stats_mode=diff[p];'
            '[b][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle[v]'
        )
        cmd = [ffmpeg_binary(), '-hide_banner', '-loglevel', 'error', '-y',
               '-i', str(self.video_path), '-filter_complex', filter_chain,
               '-map', '[v]', '-loop', '0', '-f', 'gif', str(target)]
        p = subprocess.run(cmd, capture_output=True, text=True, **no_console())
        if p.returncode or not target.is_file() or target.stat().st_size == 0:
            target.unlink(missing_ok=True)
            raise RecorderError(p.stderr.strip() or 'GIF se nepodařilo exportovat.')
        return target

    def cleanup(self):
        if self.proc:
            if self.proc.stdin:
                try:
                    self.proc.stdin.close()
                except OSError:
                    pass
            if self.proc.poll() is None:
                self.proc.kill()
                self.proc.wait()
            self.proc = None
        if self._log:
            self._log.close()
            self._log = None
        if self._temp:
            self._temp.cleanup()
            self._temp = None


class EncodingQueue:
    """Bounded producer/consumer: ffmpeg stdin can NEVER block the Qt loop."""

    def __init__(self, width: int, height: int, fps: int):
        self.session = RecordingSession(width, height, fps)
        self.session.start()
        self.queue = queue.Queue(maxsize=3)
        self.error: str | None = None
        self.dropped = 0
        self.thread = threading.Thread(target=self._run, name='gifripper-ffmpeg-io', daemon=True)
        self.thread.start()

    @property
    def paused(self):
        return self.session.paused

    @property
    def elapsed_seconds(self):
        return self.session.elapsed_seconds

    def write(self, frame: bytes):
        if self.error:
            raise RecorderError(self.error)
        try:
            self.queue.put_nowait(frame)
        except queue.Full:
            # Bounded RAM; never let high-res capture stall screen/GUI.
            self.dropped += 1

    def _run(self):
        while True:
            pixels = self.queue.get()
            if pixels is None:
                return
            try:
                self.session.write_rgba(pixels)
            except Exception as exc:
                self.error = str(exc)
                return

    def pause(self):
        self.session.pause()

    def resume(self):
        self.session.resume()

    def finalize(self, destination: str):
        """ONLY call from a background thread; can block on ffmpeg."""
        try:
            if self.thread.is_alive():
                try:
                    self.queue.put(None, timeout=10)
                except queue.Full as exc:
                    self.session.cleanup()  # terminate ffmpeg before waking blocked writer
                    raise RecorderError('FFmpeg nezvládá zapisovat snímky včas.') from exc
                self.thread.join(timeout=18)
            if self.thread.is_alive():
                self.session.cleanup()
                raise RecorderError('Zápis videa se zasekl; proces byl ukončen.')
            if self.error:
                raise RecorderError(self.error)
            self.session.stop()
            if destination:
                return str(self.session.encode_gif(destination))
            return ''
        finally:
            self.session.cleanup()

