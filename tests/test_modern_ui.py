"""Layout and backend integrity checks for the visual-only 3.2 redesign."""
from pathlib import Path
import hashlib
import os
import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_capture_backend_is_untouched_since_v31():
    # The GIF editing engine is extended by 3.3; recording code remains identical.
    # The CI working checkout need not have the 3.1 package next to it;
    # known SHA-256 prefixes are sufficient to guard source equality.
    expected = {
        'capture_agent.py':'8a8bc9caf6f28aa4',
        'capture_ipc.py':'4ced7064a88e68cf',
        'gnome_wayland.py':'2b8855c11321d564',
        'recording_flow.py':'2b0ed35b1da2e746',
        'region_selector.py':'926d339871b89f4b',
        'recorder.py':'2e397b91e8229be7',
        'x11_capture.py':'1b284593e9e19b46',
    }
    for filename, prefix in expected.items():
        assert hashlib.sha256((ROOT / filename).read_bytes()).hexdigest().startswith(prefix), filename


def test_record_and_editor_ui_are_wired_to_existing_actions():
    app = (ROOT/'app.py').read_text(encoding='utf-8')
    ui = (ROOT/'modern_ui.py').read_text(encoding='utf-8')
    assert "self.record_region_action()" in app
    assert 'w.rec_btn.clicked.connect(w.start_selected_recording)' in ui
    assert 'w.save_btn.clicked.connect(w.export_dialog)' in ui
    assert 'w.cut_btn.clicked.connect(w.cut_range)' in ui
    assert 'w.trim_before.clicked.connect(w.cut_before)' in ui
    assert 'w.trim_after.clicked.connect(w.cut_after)' in ui
    assert 'w.timeline.seek.connect(w.seek)' in ui
    assert 'w.theme_btn.clicked.connect(w.toggle_theme)' in ui


def test_qt_main_window_wires_up_on_offscreen_ci():
    pytest.importorskip('PySide6.QtWidgets')
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtWidgets import QApplication
    from app import GifRipper

    app = QApplication.instance() or QApplication([])
    window = GifRipper()
    try:
        assert window.pages.count() == 4
        assert window.pages.currentIndex() == 0
        assert len(window.inspector_tabs) == 3
        assert window.full_option.isChecked()
        assert window.rec_btn.isEnabled()
        window.show_page(1)
        assert window.pages.currentIndex() == 1
        window.show_inspector_tab(2)
        assert window.inspector_pages.currentIndex() == 2
        window.toggle_theme()
        assert window.theme in ('dark', 'light')
        window.show_page(0)
    finally:
        window.close()
