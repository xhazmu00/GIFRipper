"""Click-drag-release screen-snipping overlay for Windows.

No dialog, buttons or nested event loop. A screenshot from the SAME capture
backend is displayed on its monitor, so the selected rect maps directly to
pixels in the recorded QVideoFrame stream.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QRect, QPoint, Signal
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont
from PySide6.QtWidgets import QWidget

from recording_flow import region_from_logical_rect


class RegionSelector(QWidget):
    selected = Signal(object)  # [x, y, width, height] in physical capture pixels
    cancelled = Signal()

    def __init__(self, screenshot: QImage, screen):
        super().__init__(None, Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint)
        if screenshot.isNull():
            raise ValueError('Náhled obrazovky je prázdný.')
        self._screenshot = QPixmap.fromImage(screenshot)
        self._pixels = (screenshot.width(), screenshot.height())
        self._anchor: QPoint | None = None
        self._cursor: QPoint | None = None
        self._dragging = False
        self._message = 'Tažením myši vyber oblast  •  Esc zruší výběr'
        self.setWindowTitle('GIFRipper · Vyber oblast obrazovky')
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.CrossCursor)
        # Geometry is in Qt logical screen units. The image may use 1.25x/1.5x
        # or 2x as many physical pixels, depending on display DPI.
        self.setGeometry(screen.geometry())
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

    def _bounded(self, point: QPoint) -> QPoint:
        return QPoint(max(0, min(point.x(), self.width())),
                      max(0, min(point.y(), self.height())))

    def _rect(self) -> QRect:
        if self._anchor is None or self._cursor is None:
            return QRect()
        x1, x2 = sorted((self._anchor.x(), self._cursor.x()))
        y1, y2 = sorted((self._anchor.y(), self._cursor.y()))
        return QRect(x1, y1, x2-x1, y2-y1)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        # Draw the captured desktop edge-to-edge, not an embedded scaled dialog.
        painter.drawPixmap(self.rect(), self._screenshot)
        painter.fillRect(self.rect(), QColor(5, 12, 22, 115))
        selection = self._rect()
        if not selection.isEmpty():
            painter.save()
            painter.setClipRect(selection)
            painter.drawPixmap(self.rect(), self._screenshot)
            painter.restore()
            painter.setPen(QPen(QColor('#B8FF54'), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(selection.adjusted(0, 0, -1, -1))
            try:
                pixel_rect = region_from_logical_rect(
                    selection.left(), selection.top(), selection.right() + 1,
                    selection.bottom() + 1, self.width(), self.height(), *self._pixels)
                text = f'{pixel_rect[2]} × {pixel_rect[3]} px'
            except ValueError:
                text = 'Vyber větší oblast'
            box = QRect(selection.left(), min(self.height()-34, selection.bottom()+8), 185, 27)
            box.moveLeft(max(8, min(box.left(), self.width()-box.width()-8)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(10, 20, 31, 238))
            painter.drawRoundedRect(box, 8, 8)
            painter.setPen(QColor('#F4FFE0'))
            painter.setFont(QFont('Arial', 10, QFont.Weight.DemiBold))
            painter.drawText(box, Qt.AlignmentFlag.AlignCenter, text)
        # Small painted hint: no interactive toolbar/button obscures the image.
        width = min(475, max(210, self.width()-24))
        banner = QRect((self.width()-width)//2, 15, width, 40)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(10, 20, 31, 224))
        painter.drawRoundedRect(banner, 12, 12)
        painter.setPen(QColor('#E6F4EF'))
        painter.setFont(QFont('Arial', 10, QFont.Weight.DemiBold))
        painter.drawText(banner, Qt.AlignmentFlag.AlignCenter, self._message)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._anchor = self._bounded(event.position().toPoint())
            self._cursor = self._anchor
            self._dragging = True
            self._message = 'Pusť tlačítko myši pro potvrzení  •  Esc zruší výběr'
            self.update()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._cursor = self._bounded(event.position().toPoint())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or not self._dragging:
            return
        self._dragging = False
        self._cursor = self._bounded(event.position().toPoint())
        rect = self._rect()
        try:
            crop = region_from_logical_rect(
                rect.left(), rect.top(), rect.right()+1, rect.bottom()+1,
                self.width(), self.height(), *self._pixels)
        except ValueError:
            self._message = 'Oblast je příliš malá. Vyber alespoň 80 × 60 px  •  Esc zruší'
            self._anchor = None
            self._cursor = None
            self.update()
            return
        # Hide before notifying parent; never show the picker in the recording.
        self.hide()
        self.selected.emit(crop)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self.cancelled.emit()
            event.accept()
        else:
            super().keyPressEvent(event)
