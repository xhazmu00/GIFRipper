"""Interactive smoke tests when PySide6 is available (e.g. GitHub Actions)."""
import pytest

pytest.importorskip('PySide6')
from PySide6.QtCore import Qt, QPoint, QPointF, QEvent
from PySide6.QtGui import QImage, QMouseEvent, QKeyEvent
from PySide6.QtWidgets import QApplication
from region_selector import RegionSelector


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def mouse(widget, kind, x, y):
    event = QMouseEvent(kind, QPointF(x,y), QPointF(x,y),
                        Qt.MouseButton.LeftButton,
                        Qt.MouseButton.LeftButton if kind != QEvent.Type.MouseButtonRelease else Qt.MouseButton.NoButton,
                        Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(widget, event)


def test_drag_release_emits_pixels_and_hides(app):
    img = QImage(1920,1080,QImage.Format.Format_RGB32)
    img.fill(0x223344)
    picker = RegionSelector(img, app.primaryScreen())
    picker.resize(1536,864)
    areas = []
    picker.selected.connect(areas.append)
    picker.show()
    w, h = picker.width(), picker.height()
    drag = (int(w*.1), int(h*.1), int(w*.8), int(h*.8))
    mouse(picker, QEvent.Type.MouseButtonPress, drag[0], drag[1])
    mouse(picker, QEvent.Type.MouseMove, drag[2], drag[3])
    mouse(picker, QEvent.Type.MouseButtonRelease, drag[2], drag[3])
    from recording_flow import region_from_logical_rect
    assert areas == [region_from_logical_rect(*drag, w, h, 1920, 1080)]
    assert not picker.isVisible()
    picker.close()


def test_escape_cancels_without_starting_record(app):
    img = QImage(200,100,QImage.Format.Format_RGB32)
    img.fill(0)
    picker = RegionSelector(img, app.primaryScreen())
    cancelled, selected = [], []
    picker.cancelled.connect(lambda: cancelled.append(True))
    picker.selected.connect(selected.append)
    picker.show()
    QApplication.sendEvent(picker, QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape,
                                             Qt.KeyboardModifier.NoModifier))
    assert cancelled == [True]
    assert not selected
    assert not picker.isVisible()
    picker.close()
