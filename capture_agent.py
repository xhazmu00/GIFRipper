"""Isolated, observable screen-capture helper for GIFRipper.

Wayland: Qt Multimedia / XDG ScreenCast portal (experimental on Qt).
X11: FFmpeg's proven x11grab device, with no Qt Multimedia dependency.

A newline-delimited JSON protocol reports each step to the parent GUI.
No screen capture or video I/O is performed on the editor's GUI thread.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import traceback

os.environ.setdefault('QT_MEDIA_BACKEND', 'ffmpeg')

from PySide6.QtCore import QObject, QRect, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtMultimedia import QMediaCaptureSession, QScreenCapture, QVideoSink

from capture_ipc import encode_packet, decode_packet
from recorder import EncodingQueue, RecorderError
from x11_capture import X11FrameSource, capture_preview, is_x11_session
from gnome_wayland import GnomeWaylandRecorder, detect_backend

_SEND_LOCK = threading.Lock()


def send(event: str, **data):
    with _SEND_LOCK:
        # Byte-oriented ASCII JSON survives cp1250/cp1252 Windows codepages.
        # Unicode Czech messages are escaped and restored by JSON decoding.
        sys.stdout.buffer.write(encode_packet({'event': event, **data}))
        sys.stdout.buffer.flush()


class CommandInput(QObject):
    command = Signal(object)

    def listen(self):
        while True:
            line = sys.stdin.buffer.readline()
            if not line:
                return
            try:
                self.command.emit(decode_packet(line))
            except Exception as exc:
                send('error', message=f'Neplatný příkaz: {exc}')


class CaptureAgent(QObject):
    x11_preview_ready = Signal(str, int, int)
    x11_preview_failed = Signal(str)
    gnome_started = Signal(str)
    gnome_failed = Signal(str)

    def __init__(self, app: QGuiApplication):
        super().__init__()
        self.app = app
        self.temp = tempfile.TemporaryDirectory(prefix='gifripper-agent-')
        self.state = 'waiting'
        self.mode = ('gnome' if sys.platform.startswith('linux') and detect_backend() else
                     'x11' if sys.platform.startswith('linux') and is_x11_session() else 'qt')
        self.screen_capture = None
        self.capture_session = None
        self.sink = None
        self.latest_image: QImage | None = None
        self.rect: QRect | None = None
        self.fps = 12
        self.encoder: EncodingQueue | None = None
        self.x11: X11FrameSource | None = None
        self.gnome: GnomeWaylandRecorder | None = None
        self.last_conversion = 0.0
        self.last_frame_at = 0.0
        self.last_announcement = 0.0
        self.arming_since = 0.0
        self.last_source_warning = 0.0
        self._next_write_at = 0.0
        self._started_at = time.monotonic()
        self._platform = self.app.platformName().lower()
        self._screen_origin = (0, 0)
        self._has_reported_active = False

        self.timer = QTimer(self)
        self.timer.setInterval(125)
        self.timer.timeout.connect(self._tick)
        self.timer.start()
        self.commands = CommandInput()
        self.commands.command.connect(self._command)
        threading.Thread(target=self.commands.listen, name='gifripper-agent-input', daemon=True).start()
        self.x11_preview_ready.connect(self._x11_preview_ready)
        self.x11_preview_failed.connect(self._x11_preview_failed)
        self.gnome_started.connect(self._gnome_started)
        self.gnome_failed.connect(self._gnome_failed)

        # Create the Qt capture pipeline only if it will be used. On X11 the
        # direct ffmpeg backend is more reliable and avoids a native portal.
        if self.mode == 'qt':
            self.screen_capture = QScreenCapture(self)
            self.capture_session = QMediaCaptureSession(self)
            self.sink = QVideoSink(self)
            self.capture_session.setScreenCapture(self.screen_capture)
            self.capture_session.setVideoSink(self.sink)
            self.screen_capture.errorOccurred.connect(self._error)
            self.screen_capture.activeChanged.connect(self._active_changed)
            self.sink.videoFrameChanged.connect(self._frame)

        self.backend_label = ('GNOME Shell ScreenCast (Wayland)' if self.mode == 'gnome' else
                              'FFmpeg x11grab' if self.mode == 'x11' else
                              'Qt / ScreenCast portal' if os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland' else
                              'Qt ScreenCapture')
        send('hello', backend=self.backend_label,
             platform=os.environ.get('XDG_SESSION_TYPE', '') or sys.platform)
        QTimer.singleShot(25, self._start_capture)

    @Slot()
    def _start_capture(self):
        if self.mode == 'gnome':
            # GNOME Shell captures screen natively, no Qt frame or portal
            # permission dialog is needed. On GNOME Wayland the first Qt
            # frame can hang indefinitely. This directly arms a full-screen
            # capture, then the GUI sends start after a 3-second countdown.
            self.state = 'ready'
            send('ready_direct', backend='GNOME Shell ScreenCast',
                 message='GNOME Wayland: za 3 s začne záznam celé obrazovky (bez výběru oblasti).')
            return
        if self.mode == 'x11':
            screen = self.app.primaryScreen()
            if screen is None:
                self._error(None, 'Systém nehlásí žádnou obrazovku.')
                return
            geometry = screen.geometry()
            self._screen_origin = (geometry.x(), geometry.y())
            send('status', phase='permission', message='Zjišťuji dostupnou obrazovku X11…')
            target = str(Path(self.temp.name) / 'preview.png')
            # This is an I/O operation; do NOT run in the Qt event loop.
            def grab():
                try:
                    capture_preview(target, geometry.width(), geometry.height(),
                                    geometry.x(), geometry.y())
                    self.x11_preview_ready.emit(target, geometry.width(), geometry.height())
                except Exception as exc:
                    self.x11_preview_failed.emit(str(exc))
            threading.Thread(target=grab, name='gifripper-x11-preview', daemon=True).start()
            return

        if os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland' and 'wayland' not in self._platform:
            self._error(None, f'Qt používá {self._platform!r} místo Waylandu. '
                        'XWayland neumí zachytit celou plochu Waylandu. '
                        'Je nutný Qt Wayland plugin. Zkus nainstalovat qt6-wayland a spustit ' 
                        's QT_QPA_PLATFORM=wayland.')
            return
        send('status', phase='permission',
             message=('Čekám na systémové povolení sdílení obrazovky (Wayland)…'
                      if os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland' else
                      'Získávám náhled obrazovky přes Qt ScreenCapture…'))
        try:
            self.screen_capture.start()
        except Exception as exc:
            self._error(None, str(exc))

    @Slot(bool)
    def _active_changed(self, active):
        if active and self.state == 'waiting':
            send('status', phase='frames', message='Sdílení obrazovky je aktivní; čekám na první snímek…')
        elif not active and self.state in ('ready', 'recording'):
            # Do not flag error after an intentional stop.
            self._error(None, 'Sdílení obrazovky bylo ukončeno systémem.')

    @Slot(str, int, int)
    def _x11_preview_ready(self, path, width, height):
        if self.state != 'waiting':
            return
        self.state = 'ready'
        send('preview', path=path, width=width, height=height)

    @Slot(str)
    def _x11_preview_failed(self, reason):
        self._error(None, reason)

    @Slot(str)
    def _gnome_started(self, path):
        if self.state != 'arming':
            return
        self.state = 'recording'
        send('started', backend='GNOME Shell ScreenCast', fps=self.fps,
             width=0, height=0)

    @Slot(str)
    def _gnome_failed(self, reason):
        self._error(None, reason)

    def _error(self, _code, reason):
        if self.state in ('error', 'stopping'):
            return
        self.state = 'error'
        self.timer.stop()
        send('error', message=str(reason or 'Systémový záznam obrazovky selhal.'))

    def _frame(self, frame):
        if self.mode != 'qt' or self.state not in ('waiting', 'ready', 'recording') or not frame.isValid():
            return
        now = time.monotonic()
        self.last_frame_at = now
        if self.state != 'waiting' and now - self.last_conversion < (0.85 / self.fps if self.state == 'recording' else 2.0):
            return
        try:
            image = frame.toImage()
            if image.isNull():
                return
            self.latest_image = image.convertToFormat(QImage.Format.Format_RGBA8888).copy()
            self.last_conversion = now
            if self.state == 'waiting':
                screenshot = str(Path(self.temp.name) / 'preview.png')
                if not self.latest_image.save(screenshot, 'PNG'):
                    raise RecorderError('Nepodařilo se uložit náhled obrazovky.')
                self.state = 'ready'
                send('preview', path=screenshot, width=self.latest_image.width(), height=self.latest_image.height())
        except Exception as exc:
            self._error(None, str(exc))

    def _start_x11_region(self, x, y, w, h):
        screen = self.app.primaryScreen()
        if screen is None or x+w > screen.geometry().width() or y+h > screen.geometry().height():
            raise RecorderError('Oblast neleží na vybraném monitoru.')
        self.state = 'arming'
        self.arming_since = time.monotonic()
        send('status', phase='arming', message='Spouštím skutečný záznam obrazovky (X11)…')
        origin_x, origin_y = self._screen_origin
        self.x11 = X11FrameSource(x + origin_x, y + origin_y, w, h, self.fps)
        self.x11.start()

    @Slot(object)
    def _command(self, msg):
        action = msg.get('action')
        try:
            if action == 'start' and self.state == 'ready':
                self.fps = max(1, min(30, int(msg.get('fps', 12))))
                if self.mode == 'gnome':
                    # GNOME records entire desktop; no preview/rect is necessary.
                    # Qt's native Wayland capture may otherwise wait forever.
                    self.state = 'arming'
                    self.arming_since = time.monotonic()
                    send('status', phase='arming', message='Spouštím nativní záznam GNOME Shell…')
                    self.gnome = GnomeWaylandRecorder(self.temp.name, self.fps)
                    def launch_gnome():
                        try:
                            self.gnome_started.emit(self.gnome.start())
                        except Exception as exc:
                            self.gnome_failed.emit(str(exc))
                    threading.Thread(target=launch_gnome, name='gifripper-gnome-start', daemon=True).start()
                else:
                    rect = msg.get('rect', [])
                    if len(rect) != 4:
                        raise RecorderError('Chybí oblast záznamu.')
                    x, y, w, h = [int(v) for v in rect]
                    if w < 80 or h < 60 or x < 0 or y < 0:
                        raise RecorderError('Oblast musí mít alespoň 80 × 60 px.')
                    if self.mode == 'x11':
                        self._start_x11_region(x, y, w, h)
                    else:
                        if not self.latest_image or x+w > self.latest_image.width() or y+h > self.latest_image.height():
                            raise RecorderError('Oblast neleží uvnitř vybraného monitoru.')
                        self.rect = QRect(x, y, w, h)
                        send('status', phase='arming', message='Spouštím kódování GIFu…')
                        self.encoder = EncodingQueue(w, h, self.fps)
                        self.state = 'recording'
                        self._next_write_at = 0.0
                        self.last_conversion = 0.0
                        send('started', width=w, height=h, fps=self.fps, backend=self.backend_label)
            elif action == 'pause' and self.state == 'recording':
                if self.mode == 'gnome':
                    send('status', phase='warning', message='Systémový GNOME rekordér neumí pozastavení. Použij Zastavit.')
                    return
                if self.x11:
                    self.x11.pause()
                elif self.encoder:
                    self.encoder.pause()
                send('paused', value=True)
            elif action == 'resume' and self.state == 'recording':
                if self.mode == 'gnome':
                    return
                if self.x11:
                    self.x11.resume()
                elif self.encoder:
                    self.encoder.resume()
                send('paused', value=False)
            elif action == 'stop' and self.state == 'recording':
                self.state = 'stopping'
                if self.screen_capture:
                    self.screen_capture.stop()
                destination = str(msg.get('destination') or '')
                send('status', phase='saving', message='Ukládám záznam a vytvářím GIF…')
                writer = self.encoder
                capture = self.x11
                native = self.gnome
                def finish():
                    try:
                        if native:
                            path, frames, dropped = native.stop(destination)
                        elif capture:
                            path, frames, dropped = capture.stop(destination)
                        elif writer:
                            path = writer.finalize(destination)
                            frames, dropped = writer.session.frames, writer.dropped
                        else:
                            raise RecorderError('Interní chyba: chybí zapisovač.')
                        send('saved', path=path, frames=frames, dropped=dropped)
                    except Exception as exc:
                        send('error', message=f'Dokončení nahrávání selhalo: {exc}')
                threading.Thread(target=finish, name='gifripper-finalize', daemon=True).start()
            elif action == 'cancel':
                if self.gnome:
                    threading.Thread(target=self.gnome.close, name='gifripper-gnome-cancel', daemon=True).start()
                if self.x11:
                    self.x11.cancel()
                self.app.quit()
        except Exception as exc:
            self._error(None, str(exc))

    def _tick(self):
        now = time.monotonic()
        if self.state == 'waiting' and now - self._started_at > (38 if self.mode == 'qt' else 14):
            if self.mode == 'qt':
                if os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland':
                    self._error(None, 'Wayland nepředal žádný snímek. Ověř systémový dialog sdílení, PipeWire a xdg-desktop-portal. Qt ScreenCast může být na tomto systému nefunkční. Pomůže diagnostika diagnose.py nebo přihlášení do „Ubuntu on Xorg“.')
                else:
                    self._error(None, 'Qt nedokázalo získat žádný snímek obrazovky. Zkontroluj oprávnění aplikace pro záznam obrazovky.')
            else:
                self._error(None, 'X11 neposkytlo náhled obrazovky. Zkontroluj DISPLAY a FFmpeg.')
            return
        if self.state == 'arming' and self.gnome:
            if now - self.arming_since > 18:
                self._error(None, 'GNOME Shell neodpovědělo na žádost o záznam během 18 sekund.')
            return
        if self.state == 'arming' and self.x11:
            if self.x11.error:
                self._error(None, self.x11.error)
            elif self.x11.frames_received > 0:
                self.state = 'recording'
                send('started', width=self.x11.width, height=self.x11.height,
                     fps=self.fps, backend='FFmpeg x11grab')
            elif now - self.arming_since > 9:
                self._error(None, 'FFmpeg X11 během 9 sekund nezískal ani jeden snímek. Zkontroluj DISPLAY a oprávnění obrazovky.')
            return
        if self.state != 'recording':
            return
        if self.gnome:
            if now - self.last_announcement >= .7:
                self.last_announcement = now
                send('tick', seconds=self.gnome.elapsed_seconds, frames=0, dropped=0)
            return
        if self.x11:
            writer = self.x11.encoder
            if self.x11.error:
                self._error(None, self.x11.error)
                return
            if self.x11.last_frame_at and now - self.x11.last_frame_at > 5:
                self._error(None, 'Zdroj X11 přestal posílat snímky. Nahrávání bylo přerušeno.')
                return
        else:
            writer = self.encoder
            if writer and writer.error:
                self._error(None, writer.error)
                return
            if (writer and not writer.paused and self.rect and self.latest_image
                    and now >= self._next_write_at):
                try:
                    if not self.latest_image.rect().contains(self.rect):
                        raise RecorderError('Změnilo se rozlišení monitoru.')
                    crop = self.latest_image.copy(self.rect)
                    writer.write(bytes(crop.constBits()))
                    self._next_write_at = now + 1.0 / self.fps
                except Exception as exc:
                    self._error(None, str(exc))
                    return
            # Qt may not send new frames when the screen is static. We continue
            # using the last frame, but warn when the stream appears stalled.
            if self.last_frame_at and now - self.last_frame_at > 7 and now - self.last_source_warning > 7:
                self.last_source_warning = now
                send('status', phase='warning', message='Z Qt nepřicházejí nové snímky. Pokud se obraz na monitoru mění, záznam může být zamrzlý.')

        if writer and now - self.last_announcement >= .7:
            self.last_announcement = now
            send('tick', seconds=writer.elapsed_seconds,
                 frames=writer.session.frames, dropped=writer.dropped,
                 received=self.x11.frames_received if self.x11 else None)


def main():
    app = QGuiApplication([sys.argv[0]])
    app.setApplicationName('GIFRipper')
    app.setOrganizationName('GIFRipper')
    try:
        agent = CaptureAgent(app)
        code = app.exec()
        agent.temp.cleanup()
        return code
    except Exception:
        send('error', message=traceback.format_exc())
        return 1


if __name__ == '__main__':
    sys.exit(main())
