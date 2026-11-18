"""GIFRipper glass UI widgets, region selection and frame thumbnail timeline."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt, Signal, QRect, QRectF, QPoint, QTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QRadialGradient, QPainter, QPainterPath, QPen, QPixmap, QImage
from PySide6.QtWidgets import QWidget, QFrame, QPushButton, QLabel, QDialog, QVBoxLayout, QHBoxLayout, QSizePolicy

LIME = '#AB65FF'
TEXT = '#f5f7ff'
MUTED = '#9ca6be'
BORDER = 'rgba(204,225,255,0.14)'
ASSETS = Path(__file__).resolve().parent / 'assets'


def button(label: str, kind: str = 'neutral', size: int = 38) -> QPushButton:
    b = QPushButton(label)
    b.setObjectName({'accent': 'accent', 'danger': 'danger', 'neutral': 'neutral', 'ghost': 'ghost'}[kind])
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setMinimumHeight(size)
    return b


def tag(text: str, color: str = MUTED, size: int = 10) -> QLabel:
    l = QLabel(text)
    l.setObjectName('tag')
    role = 'start' if color.lower() == LIME.lower() else 'end' if color.lower() == '#ffb0c1' else 'normal'
    l.setProperty('role', role)
    l.setStyleSheet(f'font-size:{size}px; font-weight:700; letter-spacing:1px; background:transparent')
    return l


def pill(text: str) -> QLabel:
    l = QLabel(text)
    l.setAlignment(Qt.AlignmentFlag.AlignCenter)
    l.setObjectName('pill')
    return l


class Aurora(QWidget):
    """Animated soft light under translucent panels."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.t = 0.0
        self.theme = 'dark'
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(90)

    def set_theme(self, theme: str):
        self.theme = theme
        self.update()

    def animate(self):
        self.t += 0.018
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        if self.theme == 'light':
            grad.setColorAt(0, QColor('#E8F0FB'))
            grad.setColorAt(0.52, QColor('#F8FAFF'))
            grad.setColorAt(1, QColor('#E8F1EB'))
        else:
            grad.setColorAt(0, QColor('#070a13'))
            grad.setColorAt(0.52, QColor('#121526'))
            grad.setColorAt(1, QColor('#090d14'))
        p.fillRect(self.rect(), grad)
        glows = (
            [(116,81,202,32), (150,212,38,38), (76,154,233,39)]
            if self.theme == 'light' else
            [(110,55,202,84), (138,230,13,65), (38,110,236,50)]
        )
        for xx, yy, r, rgba in [
            (.15 + .06 * math.sin(self.t), .13, .42, glows[0]),
            (.85 + .04 * math.cos(self.t * .65), .19, .36, glows[1]),
            (.58 + .07 * math.sin(self.t * .7), .92, .47, glows[2]),
        ]:
            c = QColor(*rgba)
            radius = max(self.width(), self.height()) * r
            g = QRadialGradient(xx * self.width(), yy * self.height(), radius)
            g.setColorAt(0, c)
            g.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 0))
            p.setBrush(g)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(xx*self.width()-radius, yy*self.height()-radius, 2*radius, 2*radius))
        # soft hairline under toolbar
        p.setPen(QPen(QColor(80, 101, 140, 38) if self.theme == 'light'
                      else QColor(255, 255, 255, 19), 1))
        p.drawLine(0, 100, self.width(), 100)
        p.end()


class Stage(QWidget):
    def __init__(self):
        super().__init__()
        self.pixmap = None
        self.setMinimumSize(370, 230)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.placeholder = QPixmap()

    def set_frame(self, image: Image.Image | None):
        if image is None:
            self.pixmap = None
        else:
            rgba = image.convert('RGBA')
            data = rgba.tobytes('raw', 'RGBA')
            self.pixmap = QPixmap.fromImage(QImage(data, rgba.width, rgba.height,
                                                  rgba.width * 4, QImage.Format.Format_RGBA8888).copy())
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(r, 21, 21)
        p.setClipPath(path)
        p.fillRect(self.rect(), QColor('#11121F'))
        # fine grid and radial light
        p.setPen(QColor(186, 201, 243, 10))
        for x in range(0, self.width(), 34):
            p.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 34):
            p.drawLine(0, y, self.width(), y)
        logo = self.pixmap if self.pixmap is not None else self.placeholder
        if logo.isNull():
            p.setPen(QColor('#938CA9'))
            p.setFont(QFont('Segoe UI', 13))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 'Otevřete GIF a zobrazí se zde jeho náhled')
        if not logo.isNull():
            maxw = self.width() - (38 if self.pixmap else 110)
            maxh = self.height() - (38 if self.pixmap else 30)
            scaled = logo.scaled(max(1,maxw), max(1,maxh),
                                 Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.SmoothTransformation)
            p.drawPixmap((self.width()-scaled.width())//2, (self.height()-scaled.height())//2, scaled)
        p.setClipping(False)
        p.setPen(QPen(QColor(204, 225, 255, 25), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(r, 21, 21)
        p.end()


class Timeline(QWidget):
    """GIF frame timeline with two draggable *boundary* handles.

    The handles enclose inclusive frame indices. Display coordinates are
    proportional to frame count in Frames mode and to true GIF durations
    in Time mode; mouse hit-testing uses precisely the same mapping.
    """
    seek = Signal(int)
    set_in = Signal(int)
    set_out = Signal(int)

    def __init__(self):
        super().__init__()
        self.project = None
        self.theme = 'dark'
        self.unit = 'frames'
        self.current = self.mark_in = self.mark_out = 0
        self.setMinimumHeight(155)
        self.setMouseTracking(True)
        self._cache = {}
        self._drag_handle = None
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip('Tažením levého a pravého úchytu vyberte úsek; kliknutím jinde posunete přehrávání.')

    def set_theme(self, theme: str):
        self.theme = theme
        self.update()

    def set_unit(self, unit: str):
        if unit in ('frames', 'time'):
            self.unit = unit
            self.update()

    def set_project(self, project):
        self.project = project
        self._cache.clear()
        self._drag_handle = None
        self.current = self.mark_in = self.mark_out = 0
        self.update()

    def set_state(self, current: int, mark_in: int, mark_out: int):
        self.current, self.mark_in, self.mark_out = current, mark_in, mark_out
        self.update()

    def _fraction(self, x: float) -> float:
        return max(0.0, min(1.0, (x - 22) / max(1, self.width() - 44)))

    def x_for_boundary(self, boundary: int) -> float:
        if not self.project:
            return 22.0
        from trim_logic import boundary_fraction
        return 22 + boundary_fraction(self.project.prefix_ms, boundary, self.unit) * max(1, self.width() - 44)

    def x_for(self, index: int) -> float:
        """Start of a displayed frame (also used by the playhead)."""
        return self.x_for_boundary(index)

    def frame_at(self, x: float) -> int:
        if not self.project:
            return 0
        from trim_logic import frame_at_fraction
        return frame_at_fraction(self.project.prefix_ms, self._fraction(x), self.unit)

    def frame_for_handle(self, x: float, handle: str) -> int:
        from trim_logic import nearest_boundary
        if not self.project:
            return 0
        boundary = nearest_boundary(self.project.prefix_ms, self._fraction(x), self.unit)
        if handle == 'in':
            return min(self.project.count - 1, boundary)
        return max(0, boundary - 1)

    def thumb(self, index):
        if index not in self._cache:
            im = self.project.image(index).copy()
            im.thumbnail((152, 78), Image.Resampling.LANCZOS)
            rgba = im.convert('RGBA')
            qi = QImage(rgba.tobytes(), rgba.width, rgba.height,
                        rgba.width * 4, QImage.Format.Format_RGBA8888).copy()
            self._cache[index] = QPixmap.fromImage(qi)
            if len(self._cache) > 80:
                self._cache.pop(next(iter(self._cache)))
        return self._cache[index]

    def _selected_bounds(self):
        return self.x_for_boundary(self.mark_in), self.x_for_boundary(self.mark_out + 1)

    def _handle_at(self, x: float, y: float):
        if not self.project or not (16 <= y <= 116):
            return None
        a, b = self._selected_bounds()
        near_a = abs(x - a) <= 16
        near_b = abs(x - b) <= 16
        if near_a and near_b:
            return 'in' if abs(x - a) <= abs(x - b) else 'out'
        return 'in' if near_a else 'out' if near_b else None

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        light = self.theme == 'light'
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor('#EEE8F8') if light else QColor('#151323'))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 15, 15)
        if not self.project:
            p.setPen(QColor('#415772' if light else MUTED))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       'Otevřete GIF: táhněte levý nebo pravý fialový úchyt pro výběr úseku')
            p.end()
            return
        from trim_logic import format_timestamp
        n = self.project.count
        left, right = 22, self.width() - 22
        width = max(1, right - left)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor('#DCD5EB') if light else QColor('#24203B'))
        p.drawRoundedRect(QRectF(left, 20, width, 84), 10, 10)
        # Each thumbnail depicts the frame visible at its timeline position.
        # In Time mode a long frame may occupy multiple slots; that's correct.
        from trim_logic import frame_at_fraction
        slot_count = max(1, int(width // 106))
        cell_width = width / slot_count
        for slot in range(slot_count):
            index = frame_at_fraction(self.project.prefix_ms,
                                      (slot + 0.5) / slot_count, self.unit)
            bx = left + cell_width * slot
            box = QRectF(bx + 2, 23, max(5, cell_width - 5), 78)
            p.setBrush(QColor('#BBB3CE' if light else '#39304E'))
            p.drawRoundedRect(box, 5, 5)
            frame = self.thumb(index)
            scaled = frame.scaled(int(box.width()), int(box.height()),
                                  Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
            p.drawPixmap(int(box.center().x() - scaled.width() / 2),
                         int(box.center().y() - scaled.height() / 2), scaled)
        a, b = self._selected_bounds()
        # A selected one-frame interval has nonzero width in both modes.
        p.fillRect(QRectF(left, 20, max(0, a - left), 84), QColor(5, 5, 18, 105))
        p.fillRect(QRectF(b, 20, max(0, right - b), 84), QColor(5, 5, 18, 105))
        p.fillRect(QRectF(a, 20, max(1, b - a), 84), QColor(154, 79, 245, 52))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor('#AB65FF'), 2))
        p.drawRect(QRectF(a, 19, max(1, b - a), 86))
        # The seek/playhead marker is independent of the range handles.
        play_x = self.x_for_boundary(self.current)
        p.setPen(QPen(QColor('#192438' if light else '#FFFFFF'), 2))
        p.drawLine(int(play_x), 12, int(play_x), 112)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor('#16213B' if light else '#FFFFFF'))
        triangle = QPainterPath()
        triangle.moveTo(play_x - 6, 10)
        triangle.lineTo(play_x + 6, 10)
        triangle.lineTo(play_x, 18)
        triangle.closeSubpath()
        p.drawPath(triangle)
        # Draw paddles LAST so the white playhead never obscures their grips.
        for x, side in ((a, 'in'), (b, 'out')):
            is_dragging = self._drag_handle == side
            paddle = QRectF(x - 10, 17, 20, 91)
            p.setPen(QPen(QColor('#A85BFF'), 2))
            p.setBrush(QColor('#C99DFD' if is_dragging else '#F8F0FF'))
            p.drawRoundedRect(paddle, 7, 7)
            p.setPen(QPen(QColor('#7C36D3'), 2, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap))
            for dx in (-2, 2):
                p.drawLine(int(x + dx), 51, int(x + dx), 75)
        # Accurate ruler: seconds in Time mode, 1-based frame numbers otherwise.
        p.setFont(QFont('Segoe UI', 9, QFont.Weight.Medium))
        p.setPen(QColor('#57446A' if light else '#C8BADD'))
        if self.unit == 'time':
            begin = format_timestamp(self.project.prefix_ms[self.mark_in])
            end = format_timestamp(self.project.prefix_ms[self.mark_out + 1])
        else:
            begin, end = f'{self.mark_in + 1}', f'{self.mark_out + 1}'
        summary = f'OD {begin}     →     DO {end}'
        p.drawText(QRectF(left + 2, 112, width - 4, 18), Qt.AlignmentFlag.AlignCenter, summary)
        if self.unit == 'time':
            left_tick, right_tick = '00:00.000', format_timestamp(self.project.total_ms)
        else:
            left_tick, right_tick = '1', str(n)
        p.setFont(QFont('Segoe UI', 8))
        p.setPen(QColor('#695A7E' if light else '#9387AA'))
        p.drawText(QRectF(left, 133, width / 2, 19), Qt.AlignmentFlag.AlignLeft, left_tick)
        p.drawText(QRectF(left + width / 2, 133, width / 2, 19), Qt.AlignmentFlag.AlignRight, right_tick)
        p.end()

    def mousePressEvent(self, ev):
        if not self.project or ev.button() != Qt.MouseButton.LeftButton:
            return
        x, y = ev.position().x(), ev.position().y()
        self._drag_handle = self._handle_at(x, y)
        if self._drag_handle:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            self._move_handle(x)
        elif ev.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.set_in.emit(self.frame_at(x))
        elif ev.modifiers() & Qt.KeyboardModifier.AltModifier:
            self.set_out.emit(self.frame_at(x))
        else:
            self.seek.emit(self.frame_at(x))
        self.update()

    def _move_handle(self, x: float):
        if self._drag_handle == 'in':
            self.set_in.emit(min(self.frame_for_handle(x, 'in'), self.mark_out))
        elif self._drag_handle == 'out':
            self.set_out.emit(max(self.frame_for_handle(x, 'out'), self.mark_in))

    def mouseMoveEvent(self, ev):
        if not self.project:
            return
        x, y = ev.position().x(), ev.position().y()
        if self._drag_handle and ev.buttons() & Qt.MouseButton.LeftButton:
            self._move_handle(x)
        elif ev.buttons() & Qt.MouseButton.LeftButton:
            if ev.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.set_in.emit(self.frame_at(x))
            elif ev.modifiers() & Qt.KeyboardModifier.AltModifier:
                self.set_out.emit(self.frame_at(x))
            else:
                self.seek.emit(self.frame_at(x))
        else:
            self.setCursor(Qt.CursorShape.SizeHorCursor if self._handle_at(x, y)
                           else Qt.CursorShape.PointingHandCursor)

    def mouseReleaseEvent(self, ev):
        if self._drag_handle and ev.button() == Qt.MouseButton.LeftButton:
            self._move_handle(ev.position().x())
            self._drag_handle = None
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.update()


class RegionCanvas(QWidget):
    """Screen-sized screenshot picker; map logical cursor pixels to captured pixels."""
    selection_changed = Signal()
    resized = Signal()

    def __init__(self, image: QImage):
        super().__init__()
        self.image = image
        self.start: QPoint | None = None
        self.finish: QPoint | None = None
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def viewbox(self) -> QRectF:
        iw, ih = max(1, self.image.width()), max(1, self.image.height())
        scale = min(self.width() / iw, self.height() / ih)
        w, h = iw * scale, ih * scale
        return QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h)

    def source_point(self, pos) -> QPoint:
        view = self.viewbox()
        x = (pos.x() - view.x()) / max(1, view.width()) * self.image.width()
        y = (pos.y() - view.y()) / max(1, view.height()) * self.image.height()
        return QPoint(int(max(0, min(self.image.width() - 1, x))),
                      int(max(0, min(self.image.height() - 1, y))))

    def clear_selection(self):
        self.start = None
        self.finish = None
        self.selection_changed.emit()
        self.update()

    def selection(self) -> QRect:
        if self.start is None or self.finish is None:
            return QRect(0, 0, self.image.width(), self.image.height())
        return QRect(self.start, self.finish).normalized().intersected(self.image.rect())

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.fillRect(self.rect(), QColor('#0A101A'))
        box = self.viewbox()
        p.drawImage(box, self.image)

        if self.start is not None and self.finish is not None:
            r = self.selection()
            x = box.x() + r.x() / self.image.width() * box.width()
            y = box.y() + r.y() / self.image.height() * box.height()
            w = r.width() / self.image.width() * box.width()
            h = r.height() / self.image.height() * box.height()
            # Darken outside selected area, not the image the user is targeting.
            shade = QColor(4, 9, 19, 145)
            p.fillRect(QRectF(0, 0, self.width(), max(0, y)), shade)
            p.fillRect(QRectF(0, y, max(0, x), max(0, h)), shade)
            p.fillRect(QRectF(x + w, y, max(0, self.width() - x - w), max(0, h)), shade)
            p.fillRect(QRectF(0, y + h, self.width(), max(0, self.height() - y - h)), shade)
            p.setPen(QPen(QColor('#C4FF28'), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(QRectF(x, y, w, h))
            p.setPen(QColor('#FFFFFF'))
            p.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
            label = f'{r.width()} × {r.height()} px'
            labelw = p.fontMetrics().horizontalAdvance(label) + 20
            labelx = min(max(6, x + 5), max(6, self.width() - labelw - 6))
            labely = y + 7 if y < 38 else y - 31
            labelbox = QRectF(labelx, labely, labelw, 25)
            p.fillRect(labelbox, QColor(9, 18, 30, 220))
            p.drawText(labelbox, Qt.AlignmentFlag.AlignCenter, label)
        else:
            p.fillRect(self.rect(), QColor(0, 0, 0, 25))
        p.end()

    def mousePressEvent(self, ev):
        if ev.button() != Qt.MouseButton.LeftButton or not self.viewbox().contains(ev.position()):
            return
        self.start = self.source_point(ev.position())
        self.finish = self.start
        self.selection_changed.emit()
        self.update()

    def mouseMoveEvent(self, ev):
        if self.start is not None and ev.buttons() & Qt.MouseButton.LeftButton:
            self.finish = self.source_point(ev.position())
            self.selection_changed.emit()
            self.update()

    def mouseReleaseEvent(self, ev):
        if self.start is not None and ev.button() == Qt.MouseButton.LeftButton:
            self.finish = self.source_point(ev.position())
            self.selection_changed.emit()
            self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resized.emit()


class RegionDialog(QDialog):
    """Borderless full-screen selector with a compact floating toolbar."""
    def __init__(self, frame: QImage, parent=None):
        super().__init__(parent)
        self.setWindowTitle('GIFRipper · Vyber oblast záznamu')
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        # The capture agent records the primary screen. Map the dialog there.
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        if screen is not None and self.windowHandle() is not None:
            self.windowHandle().setScreen(screen)
        self.setStyleSheet("""
            QFrame#regionHUD, QFrame#regionActions {
                background-color: rgba(12, 20, 35, 244);
                border: 1px solid rgba(184, 211, 248, 95);
                border-radius: 15px;
            }
            QLabel#regionTitle {color:#F8FBFF; font-size:13px; font-weight:800;}
            QLabel#regionHint {color:#BFCCE1; font-size:11px;}
            QPushButton#regionCancel, QPushButton#regionWhole, QPushButton#regionStart {
                border-radius: 10px; border: 2px solid #71819E;
                background: #26364D; color: #F4F8FF;
                padding: 8px 13px; min-height: 24px;
                font-size: 12px; font-weight: 750;
            }
            QPushButton#regionCancel:hover {background:#364A65;}
            QPushButton#regionWhole {border-color:#7EC6FF; background:#173D60; color:#E9F6FF;}
            QPushButton#regionWhole:hover {background:#275982;}
            QPushButton#regionStart {border-color:#C4FF28; background:#C4FF28; color:#142206;}
            QPushButton#regionStart:hover {background:#DFFF77;}
        """)
        body = QVBoxLayout(self)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        self.canvas = RegionCanvas(frame)
        body.addWidget(self.canvas)

        self.hud = QFrame(self.canvas)
        self.hud.setObjectName('regionHUD')
        head = QVBoxLayout(self.hud)
        head.setContentsMargins(15, 10, 15, 10)
        head.setSpacing(3)
        title = QLabel('✂  GIFRipper  ·  VÝBĚR OBLASTI')
        title.setObjectName('regionTitle')
        head.addWidget(title)
        self.hint = QLabel('Táhni myší pro výběr  ·  Esc zruší')
        self.hint.setObjectName('regionHint')
        head.addWidget(self.hint)

        self.actions = QFrame(self.canvas)
        self.actions.setObjectName('regionActions')
        row = QHBoxLayout(self.actions)
        row.setContentsMargins(12, 9, 12, 9)
        row.setSpacing(9)
        cancel = button('Zrušit')
        cancel.setObjectName('regionCancel')
        cancel.clicked.connect(self.reject)
        full = button('▣  Celá obrazovka')
        full.setObjectName('regionWhole')
        full.setToolTip('Začne nahrávání celé obrazovky po 3sekundovém odpočtu')
        full.clicked.connect(self.full_screen)
        okay = button('●  Nahrát výběr', 'accent')
        okay.setObjectName('regionStart')
        okay.clicked.connect(self.accept_if_valid)
        row.addWidget(cancel)
        row.addWidget(full)
        row.addWidget(okay)

        self.canvas.selection_changed.connect(self._selection_changed)
        self.canvas.resized.connect(self._position_hud)
        QTimer.singleShot(0, self._position_hud)

    def _selection_changed(self):
        if self.canvas.start is not None and self.canvas.finish is not None:
            r = self.canvas.selection()
            self.hint.setText(f'Vybráno: {r.width()} × {r.height()} px  ·  Enter spustí')
        else:
            self.hint.setText('Táhni myší pro výběr  ·  Esc zruší')
        self._position_hud()

    def _position_hud(self):
        self.hud.adjustSize()
        self.actions.adjustSize()
        width, height = self.canvas.width(), self.canvas.height()
        self.hud.move(16, 16)
        self.actions.move(max(6, (width - self.actions.width()) // 2),
                          max(6, height - self.actions.height() - 20))
        self.hud.raise_()
        self.actions.raise_()

    def full_screen(self):
        """One click really starts full-screen recording; no separate Start needed."""
        self.canvas.clear_selection()
        self.accept_if_valid()

    def accept_if_valid(self):
        from PySide6.QtWidgets import QMessageBox
        rect = self.canvas.selection()
        if rect.width() < 80 or rect.height() < 60:
            QMessageBox.warning(self, 'Příliš malá oblast', 'Vyber alespoň 80 × 60 pixelů.')
            return
        self.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.accept_if_valid()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def selected_region(self) -> QRect:
        return self.canvas.selection()
