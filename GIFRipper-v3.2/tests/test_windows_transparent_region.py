"""Transparent overlay regression tests.

Static checks always run; the pixel and Qt window checks run on CI with PySide6.
"""
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
SELECTOR = (ROOT / 'region_selector.py').read_text(encoding='utf-8')
APP = (ROOT / 'app.py').read_text(encoding='utf-8')


def test_region_selector_uses_live_desktop_not_captured_picture():
    assert 'WA_TranslucentBackground, True' in SELECTOR
    assert 'WA_NoSystemBackground, True' in SELECTOR
    assert 'setAutoFillBackground(False)' in SELECTOR
    assert 'shade_outside_selection(painter, self.rect(), selection, shade)' in SELECTOR
    assert 'painter.drawPixmap' not in SELECTOR
    assert 'self._screenshot' not in SELECTOR
    assert 'self.selected.emit(crop)' in SELECTOR
    assert 'self.cancelled.emit()' in SELECTOR
    assert 'if self._record_mode == \'region\' and sys.platform == \'win32\':' in APP


def test_qt_shade_is_translucent_and_selection_is_clear():
    qtgui = pytest.importorskip('PySide6.QtGui')
    qtcore = pytest.importorskip('PySide6.QtCore')
    from region_selector import shade_outside_selection

    QImage, QPainter, QColor = qtgui.QImage, qtgui.QPainter, qtgui.QColor
    QRect, Qt = qtcore.QRect, qtcore.Qt
    canvas = QImage(400, 300, QImage.Format.Format_ARGB32_Premultiplied)
    canvas.fill(Qt.GlobalColor.transparent)
    painter = QPainter(canvas)
    shade_outside_selection(painter, QRect(0, 0, 400, 300),
                            QRect(100, 80, 200, 140), QColor(5, 12, 22, 68))
    painter.end()
    assert canvas.pixelColor(20, 120).alpha() == 68
    assert canvas.pixelColor(150, 100).alpha() == 0
    assert canvas.pixelColor(250, 210).alpha() == 0
    assert canvas.pixelColor(350, 120).alpha() == 68
    assert canvas.pixelColor(150, 20).alpha() == 68
    assert canvas.pixelColor(150, 270).alpha() == 68

    full = QImage(400, 300, QImage.Format.Format_ARGB32_Premultiplied)
    full.fill(Qt.GlobalColor.transparent)
    painter = QPainter(full)
    shade_outside_selection(painter, QRect(0, 0, 400, 300), QRect(), QColor(5, 12, 22, 68))
    painter.end()
    assert full.pixelColor(150, 100).alpha() == 68


def test_qt_overlay_sets_translucent_window_attributes():
    pytest.importorskip('PySide6')
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImage
    from PySide6.QtWidgets import QApplication
    from region_selector import RegionSelector
    app = QApplication.instance() or QApplication([])
    image = QImage(1920, 1080, QImage.Format.Format_ARGB32)
    image.fill(0x999999)  # Even a gray frame must never be painted onto the overlay.
    overlay = RegionSelector(image, app.primaryScreen())
    assert overlay.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    assert overlay.testAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
    assert not overlay.autoFillBackground()
    assert overlay.windowFlags() & Qt.WindowType.FramelessWindowHint
    overlay.close()
