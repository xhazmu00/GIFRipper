"""Windows screen-snipping flow: physical/logical coordinate mapping and UI wire-up.

No Qt dependency needed for geometry tests, so they can run in CI on Linux.
"""
from pathlib import Path

import pytest

from recording_flow import region_from_logical_rect, fullscreen_region

ROOT = Path(__file__).resolve().parent.parent
APP = (ROOT / 'app.py').read_text(encoding='utf-8')
AGENT = (ROOT / 'capture_agent.py').read_text(encoding='utf-8')
SELECTOR = (ROOT / 'region_selector.py').read_text(encoding='utf-8')


@pytest.mark.parametrize('logical,pixel,drag,expected', [
    ((1920, 1080), (1920, 1080), (120, 150, 780, 510), [120, 150, 660, 360]),
    ((1536, 864), (1920, 1080), (120, 80, 880, 540), [150, 100, 950, 575]),
    ((1280, 720), (1920, 1080), (100, 80, 500, 300), [150, 120, 600, 330]),
    ((1920, 1080), (3840, 2160), (20, 30, 900, 600), [40, 60, 1760, 1140]),
    ((1920, 1080), (1920, 1080), (780, 510, 120, 150), [120, 150, 660, 360]),
    ((1536, 864), (1920, 1080), (0, 0, 1536, 864), [0, 0, 1920, 1080]),
    ((1920, 1080), (1920, 1080), (-100, -50, 2500, 1800), [0, 0, 1920, 1080]),
])
def test_region_maps_logical_drag_to_physical_pixels(logical, pixel, drag, expected):
    assert region_from_logical_rect(*drag, *logical, *pixel) == expected


def test_subpixel_edge_rounds_outwards():
    assert region_from_logical_rect(0.6, 0.6, 81.1, 62.1,
                                    1920, 1080, 1920, 1080) == [0, 0, 82, 63]


@pytest.mark.parametrize('drag', [
    (10, 10, 11, 11),
    (300, 250, 300, 250),
    (0, 0, 40, 40),
    (500, 400, 0, 390),
])
def test_tiny_selections_rejected(drag):
    with pytest.raises(ValueError, match='80 × 60'):
        region_from_logical_rect(*drag, 1920, 1080, 1920, 1080)


@pytest.mark.parametrize('bad', [
    (0, 0, 80, 60, 0, 1080, 1920, 1080),
    (0, 0, 80, 60, 1920, -1, 1920, 1080),
    (float('nan'), 0, 100, 100, 1920, 1080, 1920, 1080),
])
def test_invalid_geometry_rejected(bad):
    with pytest.raises(ValueError):
        region_from_logical_rect(*bad)


def test_windows_has_two_explicit_actions():
    assert "if sys.platform == 'win32':" in APP
    assert 'Nahrát celou obrazovku' in APP
    assert 'Nahrát výseč obrazovky' in APP
    assert 'self.region_btn.clicked.connect(self.record_region_action)' in APP
    assert "self.begin_capture(mode='region')" in APP
    assert 'self.region_btn.setEnabled(not self.busy and not self.recording)' in APP


def test_record_region_selects_then_starts_the_same_capture_process():
    assert 'self.hide()\n            QTimer.singleShot(220, self._launch_capture_agent)' in APP
    assert "if self._record_mode == 'region' and sys.platform == 'win32':" in APP
    assert 'self._region_picker.selected.connect(self._region_selected)' in APP
    assert 'self._region_picker.cancelled.connect(self._region_cancelled)' in APP
    assert 'self._begin_countdown(region, direct=False)' in APP
    assert 'self._send_capture_command(\'start\'' in APP
    assert 'self._dismiss_region_picker()' in APP


def test_no_old_region_dialog_or_secondary_confirmation():
    assert 'RegionDialog' not in APP
    assert 'QDialog' not in SELECTOR
    assert 'QPushButton' not in SELECTOR
    assert 'self.selected.emit(crop)' in SELECTOR
    assert 'self.cancelled.emit()' in SELECTOR
    assert 'self.hide()\n        self.selected.emit(crop)' in SELECTOR


def test_recorded_monitor_is_primary_for_windows():
    assert "if sys.platform == 'win32' and self.app.primaryScreen() is not None:" in AGENT
    assert 'self.screen_capture.setScreen(self.app.primaryScreen())' in AGENT
    assert 'screen = QGuiApplication.primaryScreen()' in APP


def test_other_platforms_keep_original_fullscreen_backend():
    assert "if self.mode == 'gnome':" in AGENT
    assert "send('ready_direct'" in AGENT
    assert "region = fullscreen_region(packet.get('width'), packet.get('height'))" in APP
    assert fullscreen_region(1920, 1080) == [0, 0, 1920, 1080]
