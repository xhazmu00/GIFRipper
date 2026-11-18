"""Guard against bringing back the broken Windows region selection popup."""
from pathlib import Path

import pytest

from recording_flow import fullscreen_region

ROOT = Path(__file__).resolve().parent.parent
APP = (ROOT / 'app.py').read_text(encoding='utf-8')
AGENT = (ROOT / 'capture_agent.py').read_text(encoding='utf-8')


@pytest.mark.parametrize('width,height,expected', [
    (1920, 1080, [0, 0, 1920, 1080]),
    (3840, 2160, [0, 0, 3840, 2160]),
    ('2560', '1440', [0, 0, 2560, 1440]),
    (1920, 1200, [0, 0, 1920, 1200]),
])
def test_full_screen_recording_dimensions(width, height, expected):
    assert fullscreen_region(width, height) == expected


@pytest.mark.parametrize('width,height', [(None, 1080), ('oops', 1080), (0, 0), (20, 40), (1920, None)])
def test_invalid_backend_dimensions_are_reported(width, height):
    with pytest.raises(ValueError, match='rozměry obrazovky'):
        fullscreen_region(width, height)


def test_capture_preview_automatically_starts_countdown():
    assert "elif name == 'preview' and not self._agent_recording:" in APP
    assert "region = fullscreen_region(packet.get('width'), packet.get('height'))" in APP
    assert 'self._begin_countdown(region, direct=True)' in APP
    assert 'RegionDialog' not in APP
    assert 'pick_region(' not in APP
    assert 'dialog.exec()' not in APP
    assert 'self.selecting_region' not in APP


def test_three_second_countdown_remains():
    assert 'self._countdown_remaining = 3' in APP
    assert 'self._countdown_timer.start(1000)' in APP
    assert "self._send_capture_command('start'" in APP
    assert 'self.hide()' in APP


def test_recording_backends_preserved():
    assert "if self.mode == 'gnome':" in AGENT
    assert "send('ready_direct'" in AGENT
    assert "send('preview'" in AGENT
