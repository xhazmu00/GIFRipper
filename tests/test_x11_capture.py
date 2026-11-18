"""Real screen-grabber smoke tests on an isolated virtual X11 display."""
import os
from pathlib import Path
import shutil
import subprocess
import time

import pytest

from x11_capture import X11FrameSource, capture_preview, is_x11_session


def test_choose_native_backend():
    assert is_x11_session({'DISPLAY': ':0', 'XDG_SESSION_TYPE': 'x11'})
    assert is_x11_session({'DISPLAY': ':44'})
    assert not is_x11_session({'DISPLAY': ':0', 'WAYLAND_DISPLAY': 'wayland-0'})
    assert not is_x11_session({'DISPLAY': ':0', 'XDG_SESSION_TYPE': 'wayland'})
    assert not is_x11_session({'XDG_SESSION_TYPE': 'x11'})


@pytest.fixture
def x_display():
    if not (shutil.which('Xvfb') and shutil.which('ffmpeg')):
        pytest.skip('Xvfb or FFmpeg missing')
    number = f':{int(os.getpid() % 10000) + 150}'
    proc = subprocess.Popen(['Xvfb', number, '-screen', '0', '420x300x24', '-nolisten', 'tcp'],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(.4)
        if proc.poll() is not None:
            pytest.skip('Cannot start Xvfb')
        yield number
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()


def test_x11_live_record_and_gif(x_display, tmp_path):
    preview = capture_preview(tmp_path / 'screen.png', 420, 300, display=x_display)
    assert preview.stat().st_size > 100
    video = X11FrameSource(24, 40, 200, 120, 9, display=x_display)
    try:
        video.start()
        until = time.monotonic() + 8
        while video.frames_received < 2 and time.monotonic() < until:
            if video.error:
                pytest.fail(video.error)
            time.sleep(.1)
        assert video.frames_received >= 2, 'No real frames from x11grab'
        video.pause()
        time.sleep(.3)
        video.resume()
        name, frames, dropped = video.stop(str(tmp_path / 'x11.gif'))
        assert name and Path(name).stat().st_size > 100
        assert frames >= 1
        from PIL import Image
        with Image.open(name) as im:
            assert im.size == (200, 120)
            assert im.n_frames >= 1
    finally:
        video.cancel()
