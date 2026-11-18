"""GIFRipper glass UI widgets, region selection and frame thumbnail timeline."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt, Signal, QRect, QRectF, QPoint, QTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QRadialGradient, QPainter, QPainterPath, QPen, QPixmap, QImage
from PySide6.QtWidgets import QWidget, QFrame, QPushButton, QLabel, QDialog, QVBoxLayout, QHBoxLayout, QSizePolicy

LIME = '#c4ff28'
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
        self.placeholder = QPixmap(str(ASSETS / 'brand.png'))

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
        p.fillRect(self.rect(), QColor('#090d17'))
        # fine grid and radial light
        p.setPen(QColor(186, 201, 243, 10))
        for x in range(0, self.width(), 34):
            p.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 34):
            p.drawLine(0, y, self.width(), y)
        logo = self.pixmap if self.pixmap is not None else self.placeholder
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
    """Virtualized visual timeline: only visible sampled thumbnails are drawn."""
    seek = Signal(int)
    set_in = Signal(int)
    set_out = Signal(int)

    def __init__(self):
        super().__init__()
        self.project = None
        self.theme = 'dark'
        self.current = 0
        self.mark_in = 0
        self.mark_out = 0
        self.setMinimumHeight(132)
        self.setMouseTracking(True)
        self._cache = {}
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_theme(self, theme: str):
        self.theme = theme
        self.update()

    def set_project(self, project):
        self.project = project
        self._cache.clear()
        self.current = self.mark_in = self.mark_out = 0
        self.update()

    def set_state(self, current: int, mark_in: int, mark_out: int):
        self.current, self.mark_in, self.mark_out = current, mark_in, mark_out
        self.update()

    def x_for(self, i: int) -> float:
        if not self.project or self.project.count <= 1:
            return 22.0
        return 22 + i/(self.project.count-1)*max(1,self.width()-44)

    def frame_at(self, x: float) -> int:
        if not self.project:
            return 0
        pct = max(0, min(1, (x-22)/max(1,self.width()-44)))
        return round(pct * (self.project.count-1))

    def thumb(self, i):
        if i not in self._cache:
            im = self.project.image(i).copy()
            im.thumbnail((152, 78), Image.Resampling.LANCZOS)
            rgba = im.convert('RGBA')
            qi = QImage(rgba.tobytes(), rgba.width, rgba.height,
                        rgba.width*4, QImage.Format.Format_RGBA8888).copy()
            self._cache[i] = QPixmap.fromImage(qi)
            if len(self._cache) > 80:
                self._cache.pop(next(iter(self._cache)))
        return self._cache[i]

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        light = self.theme == 'light'
        p.setBrush(QColor('#D8E4F4') if light else QColor(8, 13, 26, 180))
        p.drawRoundedRect(self.rect().adjusted(1,1,-1,-1), 16, 16)
        if not self.project:
            p.setPen(QColor('#415772' if light else MUTED))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 'Otevři GIF a objeví se snímky na časové ose')
            return
        n = self.project.count
        left, right = 22, self.width()-22
        gap = 7
        h = 64
        slots = max(1, (right-left)//98)
        indices = sorted(set(round(i*(n-1)/max(1,slots-1)) for i in range(slots)))
        cellw = max(1, (right-left)/max(1,len(indices)))
        for j,i in enumerate(indices):
            x = left + j*cellw
            box = QRectF(x+2, 13, max(8,cellw-gap), h)
            p.setBrush(QColor('#AEBED3' if light else '#263041'))
            p.drawRoundedRect(box, 8,8)
            image = self.thumb(i)
            target = image.scaled(int(box.width()), int(box.height()),
                                  Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
            p.drawPixmap(int(box.center().x()-target.width()/2), int(box.center().y()-target.height()/2),target)
            p.setPen(QColor('#425874' if light else '#A3B0C8'))
            p.setFont(QFont('Inter', 8))
            p.drawText(int(x+3), 91, f'{i+1}')
            p.setPen(Qt.PenStyle.NoPen)
        # range overlay and selection bar
        a = self.x_for(min(self.mark_in,self.mark_out))
        b = self.x_for(max(self.mark_in,self.mark_out))
        p.setBrush(QColor(196,255,40,53))
        p.drawRoundedRect(QRectF(a, 102, max(3,b-a), 17), 7,7)
        for x,c in [(a,QColor('#c4ff28')),(b,QColor('#ff8c9e'))]:
            p.setPen(QPen(c,2))
            p.drawLine(int(x), 97, int(x), 123)
            p.setBrush(c)
            p.drawEllipse(QRectF(x-4, 95, 8, 8))
        x = self.x_for(self.current)
        p.setPen(QPen(QColor('#152D49' if light else '#fafcff'), 2))
        p.drawLine(int(x), 5, int(x), 127)
        p.setBrush(QColor('#152D49' if light else '#f8fbff'))
        p.setPen(Qt.PenStyle.NoPen)
        pointer = QPainterPath()
        pointer.moveTo(x-6,5)
        pointer.lineTo(x+6,5)
        pointer.lineTo(x,13)
        pointer.closeSubpath()
        p.drawPath(pointer)
        p.end()

    def mousePressEvent(self, ev):
        if not self.project:
            return
        i = self.frame_at(ev.position().x())
        if ev.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.set_in.emit(i)
        elif ev.modifiers() & Qt.KeyboardModifier.AltModifier:
            self.set_out.emit(i)
        else:
            self.seek.emit(i)

    def mouseMoveEvent(self, ev):
        if self.project and ev.buttons() & Qt.MouseButton.LeftButton:
            i = self.frame_at(ev.position().x())
            if ev.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.set_in.emit(i)
            elif ev.modifiers() & Qt.KeyboardModifier.AltModifier:
                self.set_out.emit(i)
            else:
                self.seek.emit(i)


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
