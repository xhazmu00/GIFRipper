"""UI regression tests for the Windows region-picker issues (headless-safe)."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent.parent
WIDGETS = (ROOT / 'widgets.py').read_text(encoding='utf-8')
APP = (ROOT / 'app.py').read_text(encoding='utf-8')
AGENT = (ROOT / 'capture_agent.py').read_text(encoding='utf-8')


def _method(name):
    module = ast.parse(WIDGETS)
    dialog = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == 'RegionDialog')
    return next(node for node in dialog.body if isinstance(node, ast.FunctionDef) and node.name == name)


def test_borderless_screen_overlay_not_fixed_small_dialog():
    assert 'Qt.WindowType.FramelessWindowHint' in WIDGETS
    assert 'Qt.WindowState.WindowFullScreen' in WIDGETS
    assert 'self.setMinimumSize(780, 540)' not in WIDGETS
    assert 'self.resize(980, 660)' not in WIDGETS
    assert 'self.actions = QFrame(self.canvas)' in WIDGETS


def test_full_screen_button_actually_starts_countdown():
    method = _method('full_screen')
    calls = [node.func.attr for node in ast.walk(method)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
    assert calls[-2:] == ['clear_selection', 'accept_if_valid']
    assert "full.clicked.connect(self.full_screen)" in WIDGETS
    assert 'dialog.selected_region()' in APP
    assert 'self._begin_countdown([rect.x(), rect.y(), rect.width(), rect.height()])' in APP


def test_region_select_can_start_at_zero_coordinate():
    assert 'self.start is not None' in WIDGETS
    assert 'self.start is None or self.finish is None' in WIDGETS
    assert 'if not self.start or not self.finish' not in WIDGETS


def test_mouse_coordinates_are_scaled_to_capture_resolution():
    assert 'self.image.width()' in WIDGETS
    assert 'self.image.height()' in WIDGETS
    assert 'def source_point' in WIDGETS
    assert 'view.width()' in WIDGETS
    assert 'view.height()' in WIDGETS


def test_wayland_backend_untouched_and_dialog_only_for_preview():
    assert "if self.mode == 'gnome':" in AGENT
    assert "send('ready_direct'" in AGENT
    assert "elif name == 'preview'" in APP
    assert 'dialog = RegionDialog(image, self)' in APP


def test_shortcuts_and_visible_selection_overlay():
    assert 'Qt.Key.Key_Escape' in WIDGETS
    assert 'Qt.Key.Key_Return' in WIDGETS
    assert "QColor('#C4FF28'), 2" in WIDGETS
    assert "shade = QColor(4, 9, 19, 145)" in WIDGETS
