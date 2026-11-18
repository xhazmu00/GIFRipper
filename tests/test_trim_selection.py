"""Timing conversion, both selection operations, and backend preservation."""
from pathlib import Path

import pytest
from PIL import Image

from editor import GifProject
from trim_logic import (boundary_fraction, nearest_boundary, frame_at_fraction,
                        end_frame_at_ms, start_frame_at_ms,
                        selection_duration_ms, format_timestamp)


@pytest.fixture()
def source(tmp_path):
    # Uneven durations make incorrect FPS-based calculations very obvious.
    colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff']
    images = [Image.new('RGB', (16, 16), color) for color in colors]
    path = tmp_path / 'timing.gif'
    images[0].save(path, save_all=True, append_images=images[1:],
                   duration=[100, 220, 80, 300, 100], loop=0, optimize=False)
    return path


def test_keep_only_middle_is_single_undo_step(source):
    p = GifProject(source)
    assert p.keep_range(1, 3) == 2
    assert p.kept == [1, 2, 3]
    assert p.total_ms == 600
    assert p.undo()
    assert p.kept == [0, 1, 2, 3, 4]
    assert not p.can_undo
    assert p.redo()
    assert p.kept == [1, 2, 3]
    assert p.total_ms == 600
    p.close()


def test_keep_edge_ranges_and_full_range_noop(source):
    p = GifProject(source)
    assert p.keep_range(0, 4) == 0
    assert not p.can_undo
    assert p.keep_range(0, 0) == 4
    assert p.kept == [0]
    assert p.undo() and p.kept == [0, 1, 2, 3, 4]
    assert p.keep_range(4, 4) == 4
    assert p.kept == [4]
    with pytest.raises(ValueError):
        p.keep_range(5, 6)
    with pytest.raises(ValueError):
        p.keep_range(4, 3)
    p.close()


def test_remove_selection_keeps_outer_and_is_one_undo(source):
    p = GifProject(source)
    assert p.cut(1, 3) == 3
    assert p.kept == [0, 4]
    assert p.undo() and p.count == 5
    p.close()


def test_time_mode_uses_true_frame_lengths(source):
    prefix = [0, 100, 320, 400, 700, 800]
    assert boundary_fraction(prefix, 2, 'time') == pytest.approx(0.4)
    assert boundary_fraction(prefix, 2, 'frames') == pytest.approx(0.4)
    assert boundary_fraction(prefix, 3, 'time') == pytest.approx(0.5)
    assert boundary_fraction(prefix, 3, 'frames') == pytest.approx(0.6)
    assert nearest_boundary(prefix, 0.40, 'time') == 2
    assert nearest_boundary(prefix, 0.60, 'frames') == 3
    assert nearest_boundary(prefix, 0.875, 'time') == 4
    assert frame_at_fraction(prefix, 0.40, 'time') == 2
    assert frame_at_fraction(prefix, 0.40, 'frames') == 2
    assert frame_at_fraction(prefix, 1.0, 'time') == 4
    assert frame_at_fraction(prefix, 1.0, 'frames') == 4
    assert start_frame_at_ms(prefix, 320) == 2
    assert start_frame_at_ms(prefix, 319) == 1
    assert end_frame_at_ms(prefix, 320) == 1
    assert end_frame_at_ms(prefix, 321) == 2
    assert end_frame_at_ms(prefix, 800) == 4
    assert selection_duration_ms(prefix, 1, 3) == 600
    assert format_timestamp(800) == '00:00.800'
    assert format_timestamp(61_230) == '01:01.230'


def test_keep_only_export_frame_timing_and_original(source, tmp_path):
    p = GifProject(source)
    p.keep_range(1, 3)
    dest = tmp_path / 'selected.gif'
    p.export(dest)
    q = GifProject(dest)
    assert q.count == 3
    assert q.durations == [220, 80, 300]
    assert q.total_ms == 600
    q.close()
    p.close()
    original = GifProject(source)
    assert original.count == 5
    original.close()


def test_editor_controls_and_dragging_wired_to_same_markers():
    root = Path(__file__).resolve().parent.parent
    ui = (root / 'modern_ui.py').read_text(encoding='utf-8')
    app = (root / 'app.py').read_text(encoding='utf-8')
    widgets = (root / 'widgets.py').read_text(encoding='utf-8')
    assert 'w.timeline.set_in.connect(w.change_mark_in)' in ui
    assert 'w.timeline.set_out.connect(w.change_mark_out)' in ui
    assert "w.timeline.setMinimumHeight(155)" in ui
    assert 'w.keep_btn.clicked.connect(w.keep_selected_range)' in ui
    assert 'w.cut_btn.clicked.connect(w.cut_range)' in ui
    assert "w.in_time.editingFinished.connect(lambda: w._edit_start_time(w.in_time.time()))" in ui
    assert "w.out_time.editingFinished.connect(lambda: w._edit_end_time(w.out_time.time()))" in ui
    assert "w.set_trim_unit('time')" in ui
    assert "w.set_trim_unit('frames')" in ui
    assert "self._drag_handle = self._handle_at(x, y)" in widgets
    assert "self._move_handle(ev.position().x())" in widgets
    assert 'self.project.keep_range(self.mark_in, self.mark_out)' in app


def test_qt_optional_editor_toggle_and_drag(source):
    import os
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    pytest.importorskip('PySide6.QtWidgets')
    from PySide6.QtCore import Qt, QPoint
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtWidgets import QApplication
    from app import GifRipper

    qapp = QApplication.instance() or QApplication([])
    window = GifRipper()
    try:
        window.show()
        window.open_file(source)
        qapp.processEvents()
        assert window.trim_unit in ('frames', 'time')
        window.set_trim_unit('frames')
        window.update_marks(1, 3)
        assert window.in_spin.value() == 2
        assert window.out_spin.value() == 4
        window.set_trim_unit('time')
        assert window.in_time.time().msecsSinceStartOfDay() == 100
        assert window.out_time.time().msecsSinceStartOfDay() == 700
        assert window.timeline_time_btn.isChecked()
        assert window.trim_time_btn.isChecked()
        # Mouse press/drag/release the start paddle to the start of frame 3.
        timeline = window.timeline
        timeline.show()
        qapp.processEvents()
        x0 = timeline.x_for_boundary(1)
        x1 = timeline.x_for_boundary(2)
        def mouse(kind, x, buttons):
            return QMouseEvent(kind, QPoint(round(x), 60), QPoint(round(x), 60),
                               Qt.MouseButton.LeftButton if kind != QMouseEvent.Type.MouseMove else Qt.MouseButton.NoButton,
                               buttons, Qt.KeyboardModifier.NoModifier)
        qapp.sendEvent(timeline, mouse(QMouseEvent.Type.MouseButtonPress, x0, Qt.MouseButton.LeftButton))
        qapp.sendEvent(timeline, mouse(QMouseEvent.Type.MouseMove, x1, Qt.MouseButton.LeftButton))
        qapp.sendEvent(timeline, mouse(QMouseEvent.Type.MouseButtonRelease, x1, Qt.MouseButton.NoButton))
        assert window.mark_in == 2
        window.keep_selected_range()
        assert window.project.kept == [2, 3]
        window.undo()
        assert window.project.count == 5
    finally:
        window.close()
