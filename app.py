#!/usr/bin/env python3
"""GIFRipper – floating glass cross-platform GIF recorder & frame editor.

Independent LICEcap-inspired implementation; not a fork of LICEcap.
Qt Multimedia (6.8+) captures on Linux X11/Wayland, Windows, and macOS.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import sys
import time

# Qt must use Wayland's native backend to obtain portal-mediated ScreenCast.
# Qt may otherwise run as an XWayland app and only see X11 windows.
os.environ.setdefault('QT_MEDIA_BACKEND', 'ffmpeg')
if sys.platform.startswith('linux') and os.environ.get('XDG_SESSION_TYPE','').lower() == 'wayland':
    os.environ.setdefault('QT_QPA_PLATFORM', 'wayland;xcb')

from PySide6.QtCore import Qt, QObject, Signal, Slot, QThread, QTimer, QRect, QSize, QProcess, QProcessEnvironment, QSettings
from PySide6.QtGui import QIcon, QKeySequence, QShortcut, QFont, QImage, QGuiApplication
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QHBoxLayout,
                               QVBoxLayout, QLabel, QSpinBox, QFileDialog, QMessageBox,
                               QSizePolicy, QScrollArea, QGraphicsDropShadowEffect)
from PySide6.QtGui import QColor

from capture_ipc import encode_packet, decode_packet
from recording_flow import fullscreen_region
from region_selector import RegionSelector
from editor import GifProject
from theme import PALETTES, stylesheet, inspector_action_style, inspector_field_style
from recorder import RecorderError, ffmpeg_binary
from widgets import Aurora, Stage, Timeline, button, pill, tag, ASSETS, LIME, MUTED


def fmt_ms(value: int) -> str:
    value = int(value)
    seconds, ms = divmod(value,1000)
    minutes, sec = divmod(seconds,60)
    hours, minutes = divmod(minutes,60)
    return f'{hours:02}:{minutes:02}:{sec:02}.{ms:03}' if hours else f'{minutes:02}:{sec:02}.{ms:03}'





def card(parent=None) -> QFrame:
    f = QFrame(parent)
    f.setObjectName('glass')
    return f


def drop_shadow(w):
    effect = QGraphicsDropShadowEffect(w)
    effect.setBlurRadius(45)
    effect.setOffset(0, 14)
    effect.setColor(QColor(0,0,0,95))
    w.setGraphicsEffect(effect)


class TaskWorker(QObject):
    completed = Signal(object)
    failed = Signal(str)
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
    def run(self):
        try:
            self.completed.emit(self.callback())
        except Exception as e:
            self.failed.emit(str(e))


class CaptureBar(QWidget):
    """Floating recording controls; move away from the selected region."""
    def __init__(self, main):
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.main = main
        self.setWindowTitle('GIFRipper · REC')
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(395)
        wrap = QFrame(self)
        wrap.setObjectName('glass')
        self.setStyleSheet(stylesheet(main.theme))
        lay = QVBoxLayout(self)
        lay.setContentsMargins(5,5,5,5)
        lay.addWidget(wrap)
        items = QVBoxLayout(wrap)
        items.setContentsMargins(16,12,16,14)
        items.setSpacing(10)
        row = QHBoxLayout()
        self.state = QLabel('●  NAHRÁVÁM')
        self.state.setStyleSheet('font-size:11px;font-weight:800;letter-spacing:1px')
        self.clock = QLabel('00:00.000')
        self.clock.setStyleSheet('font-size:17px;font-weight:800;')
        row.addWidget(self.state)
        row.addStretch()
        row.addWidget(self.clock)
        items.addLayout(row)
        row2 = QHBoxLayout()
        self.pause_btn = button('Ⅱ  Pauza')
        self.stop_btn = button('■  Zastavit a uložit', 'accent')
        self.pause_btn.clicked.connect(main.toggle_pause)
        self.stop_btn.clicked.connect(main.finish_capture)
        row2.addWidget(self.pause_btn)
        row2.addWidget(self.stop_btn)
        items.addLayout(row2)
        drop_shadow(wrap)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(160)
        self.apply_theme(main.theme)

    def apply_theme(self, theme: str):
        self.setStyleSheet(stylesheet(theme))
        color = '#795000' if theme == 'light' and self.main._recording_paused else (
            '#A12C48' if theme == 'light' else '#FFD394' if self.main._recording_paused else '#FF697B')
        self.state.setStyleSheet(f'color:{color};font-size:11px;font-weight:800;letter-spacing:1px')

    def tick(self):
        if self.main.recording and self.main._capture_started:
            current = self.main._capture_pause_at if self.main._recording_paused else time.monotonic()
            elapsed = max(0, current - self.main._capture_started - self.main._capture_pause_total)
            self.clock.setText(fmt_ms(elapsed*1000))

    def set_paused(self, paused):
        self.state.setText('Ⅱ  POZASTAVENO' if paused else '●  NAHRÁVÁM')
        self.apply_theme(self.main.theme)
        self.pause_btn.setText('▶  Pokračovat' if paused else 'Ⅱ  Pauza')

    def closeEvent(self, e):
        if self.main.recording and not self.main.finishing_capture:
            e.ignore()
            self.main.finish_capture()
        else:
            e.accept()


class GifRipper(QMainWindow):
    def __init__(self, initial: str | None = None):
        super().__init__()
        self.setWindowTitle('GIFRipper · Record · Slice · Create')
        self.setWindowIcon(QIcon(str(ASSETS / 'icon.png')))
        self.resize(1320, 840)
        self.setMinimumSize(1040, 720)
        self.settings = QSettings('GIFRipper', 'GIFRipper')
        saved_theme = self.settings.value('appearance/theme', 'dark')
        self.theme = saved_theme if saved_theme in PALETTES else 'dark'
        self.project: GifProject | None = None
        self.index = 0
        self.mark_in = 0
        self.mark_out = 0
        self.playing = False
        self.busy = False
        self.recording = False
        self.finishing_capture = False
        self.capture_process: QProcess | None = None
        self._agent_stdout = bytearray()
        self._agent_stderr = bytearray()
        self._capture_started = 0.0
        self._capture_pause_total = 0.0
        self._capture_pause_at = 0.0
        self._recording_paused = False
        self._agent_ready = False
        self._countdown_remaining = 0
        self._pending_capture_rect = None
        self._capture_backend = ''
        self._record_mode = 'full'
        self._region_picker: RegionSelector | None = None
        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._countdown_step)
        self._agent_recording = False
        self._agent_saved_path: str | None = None
        self._capture_phase = ''
        self._capture_status_text = ''
        self._capture_wait_started = 0.0
        self._capture_ui_timer = QTimer(self)
        self._capture_ui_timer.setInterval(1000)
        self._capture_ui_timer.timeout.connect(self._refresh_capture_status)
        self._agent_wait_timer = QTimer(self)
        self._agent_wait_timer.setSingleShot(True)
        self._agent_wait_timer.timeout.connect(self.capture_timeout)
        self.capture_bar: CaptureBar | None = None
        self._play_timer = QTimer(self)
        self._play_timer.setSingleShot(True)
        self._play_timer.timeout.connect(self.next_playback_frame)
        self.worker_thread: QThread | None = None
        self._setup_ui()
        self._apply_theme()
        self._shortcuts()
        self.update_project_ui()
        if initial:
            QTimer.singleShot(250, lambda: self.open_file(initial))

    def _setup_ui(self):
        body = Aurora(self)
        self.setCentralWidget(body)
        root = QVBoxLayout(body)
        root.setContentsMargins(25,16,25,16)
        root.setSpacing(15)
        # Brand + actions
        header = QHBoxLayout()
        header.setSpacing(14)
        icon = QLabel()
        icon.setFixedSize(66,66)
        icon.setPixmap(QIcon(str(ASSETS/'icon.png')).pixmap(QSize(64,64)))
        header.addWidget(icon)
        branding = QVBoxLayout()
        branding.setSpacing(2)
        self.brand_name = QLabel('GIFRipper')
        name = self.brand_name
        name.setStyleSheet('font-size:26px; font-weight:900; background:transparent;')
        subtitle = QLabel('CAPTURE  /  FRAME EDITOR  /  EXPORT')
        subtitle.setObjectName('subtitle')
        branding.addWidget(name)
        branding.addWidget(subtitle)
        header.addLayout(branding)
        header.addStretch()
        self.open_btn = button('↗  Otevřít GIF',size=42)
        self.rec_btn = button('●  Nahrát celou obrazovku', 'danger',size=42)
        self.region_btn = None
        # Windows offers two explicit routes. Other systems retain their
        # working fullscreen capture path (GNOME Wayland is unchanged).
        if sys.platform == 'win32':
            self.region_btn = button('▣  Nahrát výseč obrazovky', size=42)
            self.region_btn.setToolTip('Tažením myši vyber oblast. Při puštění začne odpočet.')
        self.save_btn = button('↓  Export GIF', 'accent',size=42)
        header.addWidget(self.open_btn)
        header.addWidget(self.rec_btn)
        if self.region_btn:
            header.addWidget(self.region_btn)
        header.addWidget(self.save_btn)
        self.open_btn.clicked.connect(self.open_dialog)
        self.rec_btn.clicked.connect(self.record_action)
        if self.region_btn:
            self.region_btn.clicked.connect(self.record_region_action)
        self.save_btn.clicked.connect(self.export_dialog)
        root.addLayout(header)

        # Always-visible state during capture: never leave users wondering
        # whether recording actually started or whether Qt is still waiting.
        self.capture_banner = QFrame()
        self.capture_banner.setObjectName('captureBanner')
        banner_row = QHBoxLayout(self.capture_banner)
        banner_row.setContentsMargins(15, 10, 15, 10)
        self.capture_banner_text = QLabel('Připravuji záznam…')
        self.capture_banner_text.setObjectName('bannerText')
        self.capture_banner_text.setWordWrap(True)
        banner_row.addWidget(self.capture_banner_text, 1)
        self.capture_banner_hide = button('×  Zrušit', 'ghost')
        self.capture_banner_hide.clicked.connect(self.record_action)
        banner_row.addWidget(self.capture_banner_hide)
        self.capture_banner.hide()
        root.addWidget(self.capture_banner)

        content = QHBoxLayout()
        content.setSpacing(15)
        preview_card = card()
        drop_shadow(preview_card)
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(18,15,18,15)
        preview_layout.setSpacing(10)
        title_row = QHBoxLayout()
        title_row.addWidget(tag('◈  PŘEHRÁVAČ  /  PREVIEW'))
        title_row.addStretch()
        self.file_label = pill('Bez souboru')
        title_row.addWidget(self.file_label)
        preview_layout.addLayout(title_row)
        self.stage = Stage()
        preview_layout.addWidget(self.stage,1)
        control = QHBoxLayout()
        control.setSpacing(7)
        self.first_btn = button('Ⅰ◀','neutral',38)
        self.prev_btn = button('◀','neutral',38)
        self.play_btn = button('▶  Přehrát','accent',38)
        self.stop_btn = button('■','neutral',38)
        self.next_btn = button('▶Ⅰ','neutral',38)
        self.last_btn = button('▶ⅠⅠ','neutral',38)
        self.first_btn.clicked.connect(lambda:self.seek(0))
        self.prev_btn.clicked.connect(lambda:self.seek(self.index-1))
        self.play_btn.clicked.connect(self.toggle_play)
        self.stop_btn.clicked.connect(self.stop_playback)
        self.next_btn.clicked.connect(lambda:self.seek(self.index+1))
        self.last_btn.clicked.connect(lambda:self.seek(self.project.count-1 if self.project else 0))
        for w in [self.first_btn,self.prev_btn,self.play_btn,self.stop_btn,self.next_btn,self.last_btn]:
            control.addWidget(w)
        control.addStretch()
        self.time_label = QLabel('00:00.000 / 00:00.000')
        self.time_label.setObjectName('timeText')
        control.addWidget(self.time_label)
        preview_layout.addLayout(control)
        content.addWidget(preview_card,1)

        inspector = card()
        inspector.setFixedWidth(332)
        drop_shadow(inspector)
        inspector_l = QVBoxLayout(inspector)
        inspector_l.setContentsMargins(16,17,16,15)
        inspector_l.setSpacing(12)
        inspector_l.addWidget(tag('✂  STŘIH  /  EDITOR'))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        section = QWidget()
        section.setObjectName("inspectorContent")
        section.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.inspector_section = section
        self.inspector_scroll = scroll
        section.setAutoFillBackground(True)
        scroll.viewport().setAutoFillBackground(True)
        sc = QVBoxLayout(section)
        # Gutter keeps range fields away from the clipped scroll viewport and scroll bar.
        sc.setContentsMargins(11, 10, 15, 8)
        sc.setSpacing(12)

        caps = pill('VÝBĚR ÚSEKU  ·  včetně krajních snímků')
        sc.addWidget(caps)
        line = QHBoxLayout()
        line.setSpacing(12)
        line.setContentsMargins(2, 7, 2, 6)
        one = QVBoxLayout()
        one.setSpacing(8)
        one.addWidget(tag('ZAČÁTEK  /  OD', '#c4ff28',9))
        self.in_spin = QSpinBox()
        self.in_spin.setMinimum(1)
        one.addWidget(self.in_spin)
        line.addLayout(one)
        two = QVBoxLayout()
        two.setSpacing(8)
        two.addWidget(tag('KONEC  /  DO', '#ffb0c1',9))
        self.out_spin = QSpinBox()
        self.out_spin.setMinimum(1)
        two.addWidget(self.out_spin)
        line.addLayout(two)
        sc.addLayout(line)
        self.in_spin.valueChanged.connect(lambda v:self.update_marks(v-1,self.mark_out))
        self.out_spin.valueChanged.connect(lambda v:self.update_marks(self.mark_in,v-1))
        buttons = QHBoxLayout()
        self.mark_in_btn = button('↤  Nastavit OD')
        self.mark_out_btn = button('Nastavit DO  ↦')
        self.mark_in_btn.setObjectName('inspectorAction')
        self.mark_out_btn.setObjectName('inspectorAction')
        self.mark_in_btn.setMinimumHeight(43)
        self.mark_out_btn.setMinimumHeight(43)
        self.mark_in_btn.clicked.connect(lambda: self.update_marks(self.index,self.mark_out))
        self.mark_out_btn.clicked.connect(lambda: self.update_marks(self.mark_in,self.index))
        buttons.addWidget(self.mark_in_btn)
        buttons.addWidget(self.mark_out_btn)
        sc.addLayout(buttons)
        self.cut_btn = button('✂  VYSTŘIHNOUT ÚSEK','danger',45)
        self.cut_btn.setObjectName('inspectorDanger')
        self.cut_btn.clicked.connect(self.cut_range)
        sc.addWidget(self.cut_btn)
        sc.addSpacing(7)
        sc.addWidget(tag('RYCHLÝ STŘIH'))
        self.trim_before = button('↤  Odstranit vše před snímkem')
        self.trim_after = button('Odstranit vše za snímkem  ↦')
        self.trim_before.setObjectName('inspectorAction')
        self.trim_after.setObjectName('inspectorAction')
        self.trim_before.setMinimumHeight(44)
        self.trim_after.setMinimumHeight(44)
        self.trim_before.clicked.connect(self.cut_before)
        self.trim_after.clicked.connect(self.cut_after)
        sc.addWidget(self.trim_before)
        sc.addWidget(self.trim_after)
        sc.addSpacing(7)
        sc.addWidget(tag('HISTORIE'))
        undo_row = QHBoxLayout()
        self.undo_btn = button('↶  Zpět')
        self.redo_btn = button('↷  Znovu')
        self.undo_btn.setObjectName('inspectorAction')
        self.redo_btn.setObjectName('inspectorAction')
        self.undo_btn.setMinimumHeight(43)
        self.redo_btn.setMinimumHeight(43)
        self.undo_btn.clicked.connect(self.undo)
        self.redo_btn.clicked.connect(self.redo)
        undo_row.addWidget(self.undo_btn)
        undo_row.addWidget(self.redo_btn)
        sc.addLayout(undo_row)
        self.reset_btn = button('⟳  Obnovit originál','ghost')
        self.reset_btn.setObjectName('inspectorGhost')
        self.reset_btn.setMinimumHeight(43)
        self.reset_btn.clicked.connect(self.reset)
        sc.addWidget(self.reset_btn)
        sc.addSpacing(8)
        sc.addWidget(tag('NAHRÁVÁNÍ'))
        opts = QHBoxLayout()
        opts.setSpacing(10)
        opts.setContentsMargins(2, 3, 2, 4)
        fps_label = QLabel('Snímková frekvence')
        fps_label.setObjectName('fpsLabel')
        opts.addWidget(fps_label)
        opts.addStretch()
        self.fps_spin = QSpinBox()
        self.fps_spin.setObjectName('fpsControl')
        self.fps_spin.setToolTip('Počet snímků za sekundu ve výsledném GIFu (1–30 FPS)')
        self.fps_spin.setRange(1,30)
        self.fps_spin.setValue(12)
        self.fps_spin.setSuffix(' FPS')
        self.fps_spin.setMinimumWidth(112)
        self.fps_spin.setMinimumHeight(40)
        self.fps_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        opts.addWidget(self.fps_spin)
        sc.addLayout(opts)
        sc.addStretch()
        scroll.setWidget(section)
        inspector_l.addWidget(scroll,1)
        content.addWidget(inspector)
        root.addLayout(content,1)

        timeline_card = card()
        drop_shadow(timeline_card)
        tl = QVBoxLayout(timeline_card)
        tl.setContentsMargins(15,13,15,13)
        tl.setSpacing(7)
        tl_head = QHBoxLayout()
        tl_head.addWidget(tag('▤  ČASOVÁ OSA  /  FRAMES'))
        tl_head.addStretch()
        self.frame_count_label = pill('0 SNÍMKŮ')
        tl_head.addWidget(self.frame_count_label)
        tl.addLayout(tl_head)
        self.timeline = Timeline()
        self.timeline.setMinimumHeight(115)
        self.timeline.seek.connect(self.seek)
        self.timeline.set_in.connect(lambda i: self.update_marks(i,self.mark_out))
        self.timeline.set_out.connect(lambda i: self.update_marks(self.mark_in,i))
        tl.addWidget(self.timeline)
        root.addWidget(timeline_card)
        status = QHBoxLayout()
        self.status = QLabel('●  Připraveno. Otevři GIF nebo spusť nahrávání.')
        self.status.setObjectName('statusText')
        status.addWidget(self.status)
        status.addStretch()
        status.addWidget(tag('GIFRIPPER 3.1  •   CROSS-PLATFORM', '#66738b',9))
        status.addSpacing(12)
        # Appearance is a secondary preference, deliberately kept away from
        # Open / Record / Export in the primary toolbar.
        self.theme_btn = button('☀  Světlý režim', size=33)
        self.theme_btn.setObjectName('themeToggle')
        self.theme_btn.setToolTip('Vzhled aplikace – světlý / tmavý motiv (Ctrl+L)')
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.theme_btn.setMinimumWidth(126)
        status.addWidget(self.theme_btn)
        root.addLayout(status)
        self.setStyleSheet(stylesheet(self.theme))

    def _apply_theme(self):
        # Apply app-wide theme without touching the recording or project state.
        c = PALETTES[self.theme]
        self.setStyleSheet(stylesheet(self.theme))
        self.brand_name.setText(
            f'<span style="color:{c["logo"]}">GIF</span>'
            f'<span style="color:{c["logo_green"]}">Ripper</span>')
        self.theme_btn.setText('☾  Tmavý režim' if self.theme == 'light' else '☀  Světlý režim')
        self.centralWidget().set_theme(self.theme)
        self.timeline.set_theme(self.theme)
        # Qt's scroll viewport otherwise inherits the host OS background (e.g.
        # gray on GNOME), regardless of parent Qt stylesheet.
        bg = QColor(c['bg'])
        self.inspector_section.setStyleSheet(
            f'QWidget#inspectorContent {{background:{c["bg"]}; border:none;}}')
        self.inspector_section.setAutoFillBackground(True)
        section_pal = self.inspector_section.palette()
        section_pal.setColor(self.inspector_section.backgroundRole(), bg)
        self.inspector_section.setPalette(section_pal)
        viewport = self.inspector_scroll.viewport()
        viewport.setStyleSheet(f'background:{c["bg"]}; border:none;')
        viewport.setAutoFillBackground(True)
        viewport_pal = viewport.palette()
        viewport_pal.setColor(viewport.backgroundRole(), bg)
        viewport.setPalette(viewport_pal)
        # Local control styles are deliberate: on some Wayland GNOME themes,
        # QScrollArea children lose the app-wide QPushButton background/border.
        # Assigning these after the viewport stylesheet makes the borders
        # deterministic instead of rendering the actions as naked text.
        for control, role in (
            (self.mark_in_btn, 'mark_in'),
            (self.mark_out_btn, 'mark_out'),
            (self.cut_btn, 'cut'),
            (self.trim_before, 'trim'),
            (self.trim_after, 'trim'),
            (self.undo_btn, 'history'),
            (self.redo_btn, 'history'),
            (self.reset_btn, 'reset'),
        ):
            control.setStyleSheet(inspector_action_style(self.theme, role))
        self.in_spin.setStyleSheet(inspector_field_style(self.theme, 'mark_in'))
        self.out_spin.setStyleSheet(inspector_field_style(self.theme, 'mark_out'))
        self.fps_spin.setStyleSheet(inspector_field_style(self.theme, 'fps'))
        if self.capture_bar is not None:
            self.capture_bar.apply_theme(self.theme)
        self.update()

    def toggle_theme(self):
        self.theme = 'light' if self.theme == 'dark' else 'dark'
        self.settings.setValue('appearance/theme', self.theme)
        self._apply_theme()

    def _shortcuts(self):
        commands = {
            'Ctrl+O':self.open_dialog,'Ctrl+S':self.export_dialog,
            'Ctrl+Z':self.undo,'Ctrl+Y':self.redo,
            'Ctrl+L':self.toggle_theme,
            'Space':self.toggle_play,'Left':lambda:self.seek(self.index-1),
            'Right':lambda:self.seek(self.index+1),
            'Home':lambda:self.seek(0),'End':lambda:self.seek(self.project.count-1 if self.project else 0),
            'Delete':self.cut_range,
        }
        self.shortcuts = []
        for key, cb in commands.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(cb)
            self.shortcuts.append(shortcut)

    def announce(self,text: str):
        self.status.setText('●  '+text)

    def update_project_ui(self):
        p = self.project
        loaded = p is not None
        for w in [self.save_btn,self.first_btn,self.prev_btn,self.play_btn,self.stop_btn,
                  self.next_btn,self.last_btn,self.in_spin,self.out_spin,self.mark_in_btn,
                  self.mark_out_btn,self.cut_btn,self.trim_before,self.trim_after,self.reset_btn]:
            w.setEnabled(loaded and not self.busy)
        if not loaded:
            for ctrl in [self.mark_in_btn, self.mark_out_btn, self.cut_btn,
                         self.trim_before, self.trim_after, self.undo_btn,
                         self.redo_btn, self.reset_btn]:
                ctrl.setToolTip('Nejprve otevři GIF nebo dokonči nahrávání.')
        else:
            for ctrl in [self.mark_in_btn, self.mark_out_btn, self.cut_btn,
                         self.trim_before, self.trim_after, self.undo_btn,
                         self.redo_btn, self.reset_btn]:
                ctrl.setToolTip('')
        self.undo_btn.setEnabled(loaded and p.can_undo and not self.busy)
        self.redo_btn.setEnabled(loaded and p.can_redo and not self.busy)
        self.rec_btn.setEnabled((self.recording and self.finishing_capture) or
                                (not self.busy and (not self.recording or not self._agent_recording)))
        self.rec_btn.setText('×  Zrušit dokončení' if self.finishing_capture else
                             '×  Zrušit čekání' if self.recording and not self._agent_recording else
                             '●  Nahrát celou obrazovku')
        if self.region_btn:
            self.region_btn.setEnabled(not self.busy and not self.recording)
        self.open_btn.setEnabled(not self.busy and not self.recording)
        if loaded:
            self.file_label.setText(p.path.name[:32])
            self.frame_count_label.setText(f'{p.count} SNÍMKŮ  ·  {p.size[0]}×{p.size[1]}')
            self.in_spin.blockSignals(True)
            self.out_spin.blockSignals(True)
            self.in_spin.setMaximum(p.count)
            self.out_spin.setMaximum(p.count)
            self.mark_in = max(0,min(self.mark_in,p.count-1))
            self.mark_out = max(0,min(self.mark_out,p.count-1))
            self.in_spin.setValue(self.mark_in+1)
            self.out_spin.setValue(self.mark_out+1)
            self.in_spin.blockSignals(False)
            self.out_spin.blockSignals(False)
            self.timeline.set_state(self.index,self.mark_in,self.mark_out)
            self.time_label.setText(f'{fmt_ms(p.position_ms(self.index))} / {fmt_ms(p.total_ms)}')
        else:
            self.file_label.setText('Bez souboru')
            self.frame_count_label.setText('0 SNÍMKŮ')
            self.time_label.setText('00:00.000 / 00:00.000')

    def open_dialog(self):
        if self.busy or self.recording:
            return
        file, _ = QFileDialog.getOpenFileName(self,'Otevřít GIF',str(Path.home()),'GIF animace (*.gif)')
        if file:
            self.open_file(file)

    def open_file(self,file: str | Path):
        if self.busy or self.recording:
            return
        try:
            new_project = GifProject(file)
        except Exception as e:
            QMessageBox.critical(self,'Nelze otevřít GIF',str(e))
            return
        self.stop_playback()
        if self.project:
            self.project.close()
        self.project = new_project
        self.index = self.mark_in = 0
        self.mark_out = self.project.count-1
        self.timeline.set_project(self.project)
        self.seek(0)
        self.announce(f'Otevřeno: {Path(file).name} · {self.project.count} snímků')

    def seek(self,index:int):
        if not self.project or self.busy:
            return
        self.index = max(0, min(index,self.project.count-1))
        self.stage.set_frame(self.project.image(self.index))
        self.update_project_ui()

    def toggle_play(self):
        if not self.project or self.busy:
            return
        if self.playing:
            self.stop_playback()
            return
        self.playing = True
        self.play_btn.setText('Ⅱ  Pauza')
        self._play_timer.start(max(20,self.project.duration(self.index)))

    def next_playback_frame(self):
        if not self.playing or not self.project:
            return
        self.seek((self.index+1)%self.project.count)
        self._play_timer.start(max(20,self.project.duration(self.index)))

    def stop_playback(self):
        self.playing = False
        self._play_timer.stop()
        self.play_btn.setText('▶  Přehrát')

    def update_marks(self,a:int,b:int):
        if not self.project or self.busy:
            return
        self.mark_in = max(0,min(a,self.project.count-1))
        self.mark_out = max(0,min(b,self.project.count-1))
        self.update_project_ui()

    def apply_cut(self,first:int,last:int):
        if not self.project or self.busy:
            return
        self.stop_playback()
        try:
            count = self.project.cut(first,last)
        except Exception as e:
            QMessageBox.warning(self,'Střih nebyl proveden',str(e))
            return
        self.index = min(first,self.project.count-1)
        self.mark_in,self.mark_out = 0,self.project.count-1
        self.timeline.set_project(self.project)
        self.seek(self.index)
        self.announce(f'Odstraněno {count} snímků. Ctrl+Z vrátí změnu.')

    def cut_range(self):
        if self.project:
            self.apply_cut(min(self.mark_in,self.mark_out),max(self.mark_in,self.mark_out))

    def cut_before(self):
        if self.project and self.index>0:
            self.apply_cut(0,self.index-1)

    def cut_after(self):
        if self.project and self.index<self.project.count-1:
            self.apply_cut(self.index+1,self.project.count-1)

    def undo(self):
        if self.project and not self.busy and self.project.undo():
            self.stop_playback()
            self.index = min(self.index,self.project.count-1)
            self.mark_in,self.mark_out = 0,self.project.count-1
            self.timeline.set_project(self.project)
            self.seek(self.index)
            self.announce('Střih vrácen.')

    def redo(self):
        if self.project and not self.busy and self.project.redo():
            self.stop_playback()
            self.index = min(self.index,self.project.count-1)
            self.mark_in,self.mark_out = 0,self.project.count-1
            self.timeline.set_project(self.project)
            self.seek(self.index)
            self.announce('Střih zopakován.')

    def reset(self):
        if self.project and not self.busy:
            self.project.reset()
            self.index=0
            self.mark_in,self.mark_out=0,self.project.count-1
            self.timeline.set_project(self.project)
            self.seek(0)
            self.announce('Obnoven původní stav GIFu.')

    def run_task(self, callback, finished):
        self.busy = True
        self.stop_playback()
        self.update_project_ui()
        thread = QThread(self)
        worker = TaskWorker(callback)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        # Disconnect worker thread via its own signals and return UI to ready state.
        self._task_callback = finished
        worker.completed.connect(self.task_done)
        worker.failed.connect(self.task_failed)
        worker.completed.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: setattr(self,'worker_thread',None))
        self.worker_thread = thread
        self._worker = worker
        thread.start()

    @Slot(object)
    def task_done(self, result):
        self.busy = False
        self.update_project_ui()
        self._task_callback(result)

    @Slot(str)
    def task_failed(self, message):
        self.busy = False
        self.update_project_ui()
        QMessageBox.critical(self,'Operace selhala',message)
        self.announce('Chyba: '+message)

    def export_dialog(self):
        if not self.project or self.busy:
            return
        suggested = self.project.path.with_name(self.project.path.stem+'-edit.gif')
        dest,_ = QFileDialog.getSaveFileName(self,'Uložit upravený GIF',str(suggested),'GIF animace (*.gif)')
        if not dest:
            return
        if not dest.lower().endswith('.gif'):
            dest += '.gif'
        source = self.project.path
        edited = self.project.kept.copy()
        def export():
            # Separate image decoder, safe outside GUI thread.
            clone = GifProject(source)
            try:
                clone.kept = edited
                clone._update_timeline()
                clone.export(dest)
            finally:
                clone.close()
            return dest
        self.announce('Exportuju upravený GIF…')
        self.run_task(export,lambda path:self.announce('Uloženo: '+str(path)))

    # ------- Isolated capture: Qt portal can never freeze the editor -------
    def _set_capture_status(self, phase: str, message: str):
        self._capture_phase = phase
        self._capture_status_text = message
        self.capture_banner_text.setText('◉  ' + message)
        self.capture_banner.setVisible(self.recording and not self._agent_recording)
        self.capture_banner_hide.setVisible(not self.finishing_capture)
        self.announce(message)

    def _refresh_capture_status(self):
        if not self.recording or self._agent_recording:
            return
        seconds = int(time.monotonic() - self._capture_wait_started)
        if seconds > 0:
            hint = ('  •  V systému Wayland může být potřeba potvrdit výběr monitoru.'
                    if os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland' and seconds > 6 else '')
            self.capture_banner_text.setText(
                f'◉  {self._capture_status_text}  ({seconds} s){hint}')
        if seconds >= 12 and self._capture_phase == 'permission':
            self.announce('Stále čekám na sdílení obrazovky. Hledej systémový dialog, nebo čekání zruš.')

    def record_action(self):
        if self.finishing_capture:
            self.release_capture()
            self.announce('Dokončení bylo zrušeno; rozpracovaný záznam nebyl uložen.')
        elif self.recording and not self._agent_recording:
            self.release_capture()
            self.announce('Čekání na záznam bylo zrušeno.')
        elif not self.recording:
            self.begin_capture()

    def record_region_action(self):
        if sys.platform == 'win32' and not self.recording and not self.busy:
            self.begin_capture(mode='region')

    def begin_capture(self, mode='full'):
        if self.recording or self.busy:
            return
        if mode == 'region' and sys.platform != 'win32':
            return
        try:
            ffmpeg_binary()
        except RecorderError as exc:
            QMessageBox.warning(self,'Chybí FFmpeg',str(exc))
            return
        self.stop_playback()
        self.recording = True
        self.finishing_capture = False
        self._agent_recording = False
        self._agent_ready = False
        self._agent_saved_path = None
        self._countdown_timer.stop()
        self._pending_capture_rect = None
        self._capture_backend = ''
        self._record_mode = mode
        self._agent_stdout.clear()
        self._agent_stderr.clear()
        self._recording_paused = False
        self._capture_started = 0.0
        self._capture_pause_total = 0.0
        self._capture_pause_at = 0.0
        self._capture_wait_started = time.monotonic()
        self._set_capture_status('launch', 'Spouštím pomocný proces nahrávání…')
        self._capture_ui_timer.start()
        if mode == 'region':
            # Hide before the helper takes its preview. Otherwise the screenshot
            # contains GIFRipper itself instead of the intended desktop.
            self.hide()
            QTimer.singleShot(220, self._launch_capture_agent)
        else:
            self._launch_capture_agent()
        self.update_project_ui()

    def _launch_capture_agent(self):
        if not self.recording or self.capture_process is not None:
            return
        proc = QProcess(self)
        self.capture_process = proc
        proc.readyReadStandardOutput.connect(self._read_agent_stdout)
        proc.readyReadStandardError.connect(self._read_agent_stderr)
        proc.finished.connect(self._agent_exited)
        proc.errorOccurred.connect(self._agent_process_error)
        if sys.platform.startswith('linux') and os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland':
            environment = QProcessEnvironment.systemEnvironment()
            # Qt may fall back to XWayland with 'wayland;xcb' and silently
            # capture no real desktop. Use native Wayland in the helper only.
            environment.insert('QT_QPA_PLATFORM', 'wayland')
            proc.setProcessEnvironment(environment)
        if getattr(sys, 'frozen', False):
            proc.start(sys.executable, ['--capture-agent'])
        else:
            proc.start(sys.executable, ['-u', str(Path(__file__).resolve().parent/'capture_agent.py')])
        self._agent_wait_timer.start(12000 if os.environ.get('XDG_SESSION_TYPE','').lower() == 'wayland' else 23000)
        description = ('Pořizuji snímek monitoru pro výběr výseče…'
                       if self._record_mode == 'region' else
                       'Připravuji záznam celé obrazovky / případné systémové povolení…')
        self._set_capture_status('permission', description)

    def _send_capture_command(self, action: str, **data):
        proc = self.capture_process
        if proc and proc.state() == QProcess.ProcessState.Running:
            proc.write(encode_packet({'action': action, **data}))
            return True
        return False

    def _read_agent_stdout(self):
        proc = self.capture_process
        if not proc:
            return
        self._agent_stdout.extend(bytes(proc.readAllStandardOutput()))
        # Cap pathological child output if something goes wrong.
        if len(self._agent_stdout) > 6_000_000:
            self.fail_capture('Proces nahrávání odeslal příliš mnoho dat.')
            return
        while b'\n' in self._agent_stdout:
            line, _, rest = self._agent_stdout.partition(b'\n')
            self._agent_stdout = bytearray(rest)
            try:
                self._handle_capture_event(decode_packet(line))
            except (ValueError, UnicodeDecodeError) as exc:
                self.fail_capture('Nekompatibilní odpověď procesu záznamu: '+str(exc))
                return

    def _read_agent_stderr(self):
        if self.capture_process:
            self._agent_stderr.extend(bytes(self.capture_process.readAllStandardError()))
            if len(self._agent_stderr) > 150_000:
                self._agent_stderr = self._agent_stderr[-150_000:]

    def _handle_capture_event(self, packet):
        if not self.recording:
            return
        name = packet.get('event')
        if name == 'hello':
            backend = packet.get('backend', 'neznámý')
            self._set_capture_status('permission', f'Backend {backend} je spuštěný. Čekám na přístup k obrazovce…')
        elif name == 'status':
            self._set_capture_status(str(packet.get('phase', 'waiting')),
                                     str(packet.get('message') or 'Čekám na obrazovku…'))
        elif name == 'ready_direct' and not self._agent_recording:
            self._agent_wait_timer.stop()
            self._capture_backend = str(packet.get('backend') or '')
            self._begin_countdown(None, direct=True)
        elif name == 'preview' and not self._agent_recording:
            self._agent_wait_timer.stop()
            self._agent_ready = True
            if self._record_mode == 'region' and sys.platform == 'win32':
                self._show_region_selector(packet)
                return
            try:
                region = fullscreen_region(packet.get('width'), packet.get('height'))
            except ValueError as exc:
                self.fail_capture(str(exc))
                return
            self._begin_countdown(region, direct=True)
        elif name == 'started':
            self._countdown_timer.stop()
            self._capture_backend = str(packet.get('backend') or '')
            self._agent_wait_timer.stop()
            self._capture_ui_timer.stop()
            self.capture_banner.hide()
            self._agent_recording = True
            self._capture_started = time.monotonic()
            self._capture_pause_total = 0.0
            self._recording_paused = False
            self.capture_bar = CaptureBar(self)
            if 'GNOME Shell' in self._capture_backend:
                self.capture_bar.pause_btn.hide()
                self.capture_bar.stop_btn.setToolTip('GNOME nativní záznam: pauza zatím není podporována. Zastav a ulož GIF.')
            desktop = QGuiApplication.primaryScreen().availableGeometry()
            self.capture_bar.move(desktop.right() - self.capture_bar.width() - 24,
                                  desktop.bottom() - 150)
            self.capture_bar.show()
            self.hide()
            self.announce('Nahrávání skutečně začalo. Ovládání je v plovoucím okně.')
            self.update_project_ui()
        elif name == 'paused':
            if self.capture_bar:
                self.capture_bar.set_paused(bool(packet.get('value')))
        elif name == 'tick':
            dropped = int(packet.get('dropped') or 0)
            if dropped:
                self.announce(f'Nahrávám · {packet.get("frames",0)} snímků · přeskočeno {dropped} (vysoké zatížení).')
        elif name == 'saved':
            path = str(packet.get('path') or '')
            dropped = int(packet.get('dropped') or 0)
            self.release_capture()
            self.finishing_capture = False
            if path:
                self.open_file(path)
                self.announce('Nový GIF byl uložen a otevřen v editoru.' +
                              (f' Vynecháno {dropped} snímků kvůli výkonu.' if dropped else ''))
            else:
                self.announce('Záznam byl ukončen bez uložení souboru.')
        elif name == 'error':
            self.fail_capture(str(packet.get('message') or 'Neznámá chyba záznamu.'))

    def _show_region_selector(self, packet):
        try:
            path = str(packet.get('path') or '')
            image = QImage(path)
            if image.isNull():
                raise ValueError('Z procesu nahrávání nelze načíst náhled obrazovky.')
            # Match the exact preview dimensions to avoid recording another
            # monitor, or a crop shifted by DPI scaling.
            dimensions = fullscreen_region(packet.get('width'), packet.get('height'))
            if image.width() != dimensions[2] or image.height() != dimensions[3]:
                raise ValueError('Rozměry náhledu nesouhlasí s nahrávanou obrazovkou.')
            screen = QGuiApplication.primaryScreen()
            if screen is None:
                raise ValueError('Windows nevrací žádný aktivní monitor.')
            self._region_picker = RegionSelector(image, screen)
            self._region_picker.selected.connect(self._region_selected)
            self._region_picker.cancelled.connect(self._region_cancelled)
            self._region_picker.show()
            self._region_picker.raise_()
            self._region_picker.activateWindow()
            self._region_picker.setFocus()
            self._set_capture_status('selection', 'Tažením myši vyber oblast. Esc výběr zruší.')
        except Exception as exc:
            self.fail_capture('Výběr oblasti nelze otevřít: ' + str(exc))

    def _dismiss_region_picker(self):
        picker = self._region_picker
        self._region_picker = None
        if picker is not None:
            picker.hide()
            picker.deleteLater()

    def _region_selected(self, region):
        if not self.recording or self._record_mode != 'region':
            return
        self._dismiss_region_picker()
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self._begin_countdown(region, direct=False)

    def _region_cancelled(self):
        if self.recording:
            self.release_capture()
            self.announce('Výběr výseče byl zrušen.')

    def _begin_countdown(self, region, direct=False):
        """A real 3 s countdown BEFORE invoking screen recording."""
        if not self.recording:
            return
        self._pending_capture_rect = region
        self._countdown_remaining = 3
        self._agent_wait_timer.stop()
        mode = 'celé obrazovky' if direct else 'vybrané oblasti'
        self._set_capture_status('countdown', f'Záznam {mode} začne za 3…')
        self._countdown_timer.start(1000)

    def _countdown_step(self):
        if not self.recording:
            self._countdown_timer.stop()
            return
        self._countdown_remaining -= 1
        if self._countdown_remaining > 0:
            self._set_capture_status('countdown',
                f'Záznam začne za {self._countdown_remaining}…')
            return
        self._countdown_timer.stop()
        self._set_capture_status('arming', 'Spouštím skutečný záznam obrazovky…')
        self._agent_wait_timer.start(22000)
        # Hide the editor BEFORE the native GNOME screencaster starts.
        self.hide()
        if not self._send_capture_command('start',
                rect=self._pending_capture_rect or [], fps=self.fps_spin.value()):
            self.fail_capture('Pomocný proces nahrávání skončil před startem.')

    def capture_timeout(self):
        if self.recording:
            diagnostics = self._agent_stderr.decode('utf-8', 'replace').strip()[-1300:]
            if self.finishing_capture:
                reason = 'Dokončení záznamu překročilo časový limit.'
            elif self._capture_phase == 'arming':
                reason = 'Po odpočtu nepřišel žádný živý snímek. Nahrávání se nespustilo.'
            elif os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland':
                reason = ('Záznam nedostal během několika sekund snímek z Waylandu. '
                          'Zkontroluj systémový výběr monitoru, PipeWire a xdg-desktop-portal. '
                          'Qt ScreenCast je na Waylandu experimentální. '
                          'Pokud selhává opakovaně, přihlas se do „Ubuntu on Xorg“.')
            else:
                reason = 'Nahrávání nedostalo snímek obrazovky. Zkontroluj FFmpeg a DISPLAY.' 
            self.fail_capture(reason + (f'\n\nTechnické podrobnosti:\n{diagnostics}' if diagnostics else ''))

    def _agent_process_error(self, _error):
        if self.recording:
            self.fail_capture('Nepodařilo se spustit proces nahrávání. '
                              'Zkontroluj instalaci PySide6.QtMultimedia.')

    def _agent_exited(self, exit_code, _exit_status):
        if self.recording:
            diagnostics = self._agent_stderr.decode('utf-8', 'replace').strip()[-1200:]
            self.fail_capture(f'Proces nahrávání neočekávaně skončil (kód {exit_code}).'
                              + (f'\n\n{diagnostics}' if diagnostics else ''))

    def toggle_pause(self):
        if not self.recording or not self._agent_recording or self.finishing_capture:
            return
        if 'GNOME Shell' in self._capture_backend:
            return
        now = time.monotonic()
        if self._recording_paused:
            if self._send_capture_command('resume'):
                self._capture_pause_total += now - self._capture_pause_at
                self._recording_paused = False
        else:
            if self._send_capture_command('pause'):
                self._capture_pause_at = now
                self._recording_paused = True
        if self.capture_bar:
            self.capture_bar.set_paused(self._recording_paused)

    def finish_capture(self):
        if not self.recording or not self._agent_recording or self.finishing_capture:
            return
        self.finishing_capture = True
        if not self._recording_paused and 'GNOME Shell' not in self._capture_backend:
            self.toggle_pause_for_finalize()
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.clear_capture_controls()
        suggested = Path.home() / 'Videos' / 'GIFRipper' / f'GIFRipper-{datetime.now():%Y%m%d-%H%M%S}.gif'
        suggested.parent.mkdir(parents=True, exist_ok=True)
        destination, _ = QFileDialog.getSaveFileName(self, 'Uložit GIF nahrávku', str(suggested), 'GIF animace (*.gif)')
        if destination and not destination.lower().endswith('.gif'):
            destination += '.gif'
        self.announce('Dokončuji video a převádím ho na GIF (editor zůstává ovladatelný)…')
        self._agent_wait_timer.start(150000)
        self.busy = True
        self.update_project_ui()
        if not self._send_capture_command('stop', destination=destination):
            self.fail_capture('Proces nahrávání se předčasně ukončil.')

    def toggle_pause_for_finalize(self):
        self._send_capture_command('pause')
        self._recording_paused = True
        self._capture_pause_at = time.monotonic()

    def clear_capture_controls(self):
        if self.capture_bar:
            bar = self.capture_bar
            self.capture_bar = None
            bar.close()
            bar.deleteLater()

    def release_capture(self):
        self._agent_wait_timer.stop()
        self._capture_ui_timer.stop()
        self._countdown_timer.stop()
        self.capture_banner.hide()
        self.recording = False
        self._pending_capture_rect = None
        self._dismiss_region_picker()
        self._agent_recording = False
        self._agent_ready = False
        self.finishing_capture = False
        self.busy = False
        self.clear_capture_controls()
        proc = self.capture_process
        self.capture_process = None
        if proc:
            # Disconnect our old process before starting another capture.
            for signal, slot in (
                (proc.readyReadStandardOutput, self._read_agent_stdout),
                (proc.readyReadStandardError, self._read_agent_stderr),
                (proc.finished, self._agent_exited),
                (proc.errorOccurred, self._agent_process_error),
            ):
                try:
                    signal.disconnect(slot)
                except (TypeError, RuntimeError):
                    pass
            if proc.state() != QProcess.ProcessState.NotRunning:
                proc.kill()
            # Never waitForFinished() on the UI thread: even a wedged native
            # screen-capture backend must not freeze the GUI.
            proc.finished.connect(proc.deleteLater)
            if proc.state() == QProcess.ProcessState.NotRunning:
                proc.deleteLater()
        self.showNormal()
        self.update_project_ui()

    def fail_capture(self, reason):
        if not self.recording:
            return
        self.release_capture()
        QMessageBox.critical(self, 'Nahrávání selhalo', str(reason))
        self.announce('Nahrávání skončilo chybou.')

    def closeEvent(self,event):
        if self.recording:
            event.ignore()
            QMessageBox.information(self,'Probíhá záznam','Nejdřív zastav nahrávání.')
        elif self.busy:
            event.ignore()
            QMessageBox.information(self,'Probíhá export','Dokončuji export. Okno zatím nezavírej.')
        else:
            self.stop_playback()
            if self.project:
                self.project.close()
            event.accept()


def main():
    # PyInstaller standalone executable doubles as the isolated capture agent.
    if '--capture-agent' in sys.argv:
        from capture_agent import main as capture_main
        sys.exit(capture_main())
    app = QApplication(sys.argv)
    app.setApplicationName('GIFRipper')
    app.setOrganizationName('GIFRipper')
    app.setStyle('Fusion')
    app.setFont(QFont('Inter',10))
    app.setWindowIcon(QIcon(str(ASSETS/'icon.png')))
    window = GifRipper(sys.argv[1] if len(sys.argv)>1 else None)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
