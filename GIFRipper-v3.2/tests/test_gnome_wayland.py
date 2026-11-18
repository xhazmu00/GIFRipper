"""Test backend selection and media conversion; doesn't require a real GNOME session."""
import shutil
import subprocess
from pathlib import Path

import pytest

from gnome_wayland import detect_backend, is_gnome_wayland, _gif_from_video
from recorder import RecorderError


def test_gnome_detection():
    assert is_gnome_wayland({'XDG_CURRENT_DESKTOP':'ubuntu:GNOME', 'XDG_SESSION_TYPE':'wayland'})
    assert not is_gnome_wayland({'XDG_CURRENT_DESKTOP':'GNOME', 'XDG_SESSION_TYPE':'x11'})
    assert not is_gnome_wayland({'XDG_CURRENT_DESKTOP':'KDE', 'XDG_SESSION_TYPE':'wayland'})
    assert detect_backend({'XDG_CURRENT_DESKTOP':'GNOME', 'XDG_SESSION_TYPE':'wayland'})
    assert not detect_backend({'XDG_CURRENT_DESKTOP':'GNOME', 'XDG_SESSION_TYPE':'wayland', 'GIFRIPPER_WAYLAND_BACKEND':'qt'})


def test_gnome_gif_requires_valid_video(tmp_path):
    with pytest.raises(RecorderError, match='video'):
        _gif_from_video(tmp_path/'missing.webm', str(tmp_path/'result.gif'), 12)


@pytest.mark.skipif(not shutil.which('ffmpeg'), reason='FFmpeg unavailable')
def test_gnome_webm_to_gif(tmp_path):
    source = tmp_path/'recorded.webm'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
                    '-f','lavfi','-i','testsrc2=size=128x80:rate=10:duration=1',
                    '-c:v','libvpx-vp9','-b:v','500k',str(source)],check=True)
    gif_path = tmp_path/'result.gif'
    _gif_from_video(source,str(gif_path),10)
    assert gif_path.stat().st_size > 100
    from PIL import Image
    with Image.open(gif_path) as image:
        assert image.n_frames >= 5
        assert image.size == (128,80)


def test_gnome_records_and_stops_on_same_dbus_connection(tmp_path, monkeypatch):
    """GNOME insists that recording stops from the original D-Bus sender."""
    import sys
    import types
    import gnome_wayland as gw

    events = []

    class FakeVariant:
        def __init__(self, signature, value):
            self.signature = signature
            self.value = value

    class FakeInterface:
        async def call_screencast(self, template, options):
            events.append(('start', template, options['framerate'].value))
            Path(template).write_bytes(b'x' * 200)
            return True, template

        async def call_stop_screencast(self):
            events.append(('stop',))
            return True

    class FakeProxy:
        def get_interface(self, interface):
            assert interface == gw.INTERFACE
            return FakeInterface()

    class FakeBus:
        async def connect(self):
            events.append(('connect',))
            return self

        async def introspect(self, bus, path):
            events.append(('introspect', bus, path))
            return object()

        def get_proxy_object(self, *_args):
            return FakeProxy()

        def disconnect(self):
            events.append(('disconnect',))

    fake_pkg = types.ModuleType('dbus_next')
    fake_pkg.Variant = FakeVariant
    fake_aio = types.ModuleType('dbus_next.aio')
    fake_aio.MessageBus = FakeBus
    monkeypatch.setitem(sys.modules, 'dbus_next', fake_pkg)
    monkeypatch.setitem(sys.modules, 'dbus_next.aio', fake_aio)
    monkeypatch.setattr(gw, '_gif_from_video', lambda _video, dest, _fps: dest)

    recorder = gw.GnomeWaylandRecorder(str(tmp_path), fps=12)
    try:
        assert recorder.start().endswith('gnome-capture.webm')
        assert recorder.active
        assert recorder.stop(str(tmp_path/'captured.gif'))[0].endswith('captured.gif')
        assert [e[0] for e in events].count('start') == 1
        assert [e[0] for e in events].count('stop') == 1
        assert events.index(('stop',)) < events.index(('disconnect',))
    finally:
        recorder.close()
