"""The mockup-inspired GIFRipper presentation, deliberately separate from capture.

The controls preserve the main window's existing public widget handles, so the
original capture agent, selection overlay, project methods, and export remain intact.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget,
    QPushButton, QSpinBox, QTimeEdit, QScrollArea, QSizePolicy, QFileDialog,
)

from widgets import Stage, Timeline, button, pill, tag, ASSETS
from modern_theme import modern_stylesheet, COLORS
from theme import inspector_action_style, inspector_field_style


def label(text, name=None, wrap=False):
    w = QLabel(text)
    if name:
        w.setObjectName(name)
    w.setWordWrap(wrap)
    return w


def panel():
    w = QFrame()
    w.setObjectName('panel')
    return w


def row(spacing=10):
    lay = QHBoxLayout()
    lay.setSpacing(spacing)
    return lay


def col(spacing=10):
    lay = QVBoxLayout()
    lay.setSpacing(spacing)
    return lay


def nav_button(title):
    b = QPushButton(title)
    b.setObjectName('navButton')
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setCheckable(True)
    b.setMinimumHeight(56)
    return b


def unit_toggle(text):
    b = QPushButton(text)
    b.setObjectName('unitToggle')
    b.setCheckable(True)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setMinimumHeight(34)
    b.setMinimumWidth(76)
    return b


def trim_unit_buttons(w, prefix):
    """Two synchronized mode switches, both backed by selected frame indices."""
    line = row(5)
    frames = unit_toggle('▤  Snímky')
    times = unit_toggle('◷  Čas')
    setattr(w, prefix + '_frames_btn', frames)
    setattr(w, prefix + '_time_btn', times)
    frames.clicked.connect(lambda: w.set_trim_unit('frames'))
    times.clicked.connect(lambda: w.set_trim_unit('time'))
    line.addWidget(frames)
    line.addWidget(times)
    return line


def setup_modern_ui(w):
    w.resize(1390, 860)
    w.setMinimumSize(1050, 700)
    shell = QWidget()
    shell.setObjectName('shell')
    w.setCentralWidget(shell)
    outer = QHBoxLayout(shell)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)

    side = QFrame()
    side.setObjectName('sidebar')
    side.setFixedWidth(236)
    sidebar_layout = col(18)
    sidebar_layout.setContentsMargins(21, 18, 20, 16)
    side.setLayout(sidebar_layout)
    brand = row(11)
    icon = label('GIF')
    icon.setFixedSize(45, 45)
    icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon.setStyleSheet('background:#8F41EF;color:white;border-radius:11px;font-weight:900;font-size:15px;')
    brand.addWidget(icon)
    w.brand_name = label('GIFRipper', 'brand')
    brand.addWidget(w.brand_name)
    brand.addStretch()
    sidebar_layout.addLayout(brand)
    sidebar_layout.addSpacing(25)
    w.nav_buttons = [nav_button(x) for x in (
        '▣   Nahrávání', '✂   Upravit GIF', '▤   Moje GIFy', '⚙   Nastavení')]
    for index, b in enumerate(w.nav_buttons):
        b.clicked.connect(lambda _=False, i=index: w.show_page(i))
        sidebar_layout.addWidget(b)
    sidebar_layout.addStretch()
    sidebar_layout.addWidget(label('GIFRIPPER  •  DESKTOP', 'small'))
    outer.addWidget(side)

    content = QWidget()
    content_layout = col(0)
    content_layout.setContentsMargins(0, 0, 0, 0)
    content.setLayout(content_layout)
    w.pages = QStackedWidget()
    content_layout.addWidget(w.pages, 1)
    footer = QFrame()
    footer.setObjectName('topBrand')
    foot = row(8)
    foot.setContentsMargins(24, 7, 24, 8)
    footer.setLayout(foot)
    w.status = label('●  Připraveno', 'statusText')
    foot.addWidget(w.status, 1)
    w.theme_btn = button('☀  Světlý režim')
    w.theme_btn.setObjectName('themeToggle')
    w.theme_btn.setToolTip('Změnit motiv (Ctrl+L)')
    w.theme_btn.clicked.connect(w.toggle_theme)
    foot.addWidget(w.theme_btn)
    content_layout.addWidget(footer)
    outer.addWidget(content, 1)

    _make_record_page(w)
    _make_editor_page(w)
    _make_library_page(w)
    _make_settings_page(w)

    # Recording state visible across all views; do not change capture logic.
    w.capture_banner = QFrame()
    w.capture_banner.setObjectName('captureBanner')
    banner = row(12)
    banner.setContentsMargins(13, 10, 13, 10)
    w.capture_banner.setLayout(banner)
    w.capture_banner_text = label('Připravuji záznam…', 'bannerText', wrap=True)
    banner.addWidget(w.capture_banner_text, 1)
    w.capture_banner_hide = button('✕  Zrušit')
    w.capture_banner_hide.clicked.connect(w.record_action)
    banner.addWidget(w.capture_banner_hide)
    # Keep the capture banner visible on whichever page the user is on.
    content_layout.insertWidget(0, w.capture_banner)
    w.capture_banner.hide()
    w.show_page(0)
    w.setStyleSheet(modern_stylesheet(w.theme))
    w.set_trim_unit(w.trim_unit)


def _make_record_page(w):
    page = QWidget()
    l = col(23)
    l.setContentsMargins(48, 40, 48, 30)
    page.setLayout(l)
    l.addSpacing(5)
    l.addWidget(label('Vytvořit GIF z nahrávky', 'heading'))
    l.addWidget(label('Nahrajte obrazovku a automaticky ji převeďte do GIFu.', 'body'))
    l.addSpacing(12)
    options = row(22)
    w.full_option = QPushButton('▣\n\nNahrát celou obrazovku\n\nZaznamenat celý monitor')
    w.full_option.setObjectName('recordOption')
    w.full_option.setCheckable(True)
    w.full_option.setCursor(Qt.CursorShape.PointingHandCursor)
    w.full_option.setMinimumHeight(245)
    w.full_option.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    w.full_option.clicked.connect(lambda: w.select_record_mode('full'))
    options.addWidget(w.full_option, 1)
    w.region_btn = None
    if sys.platform == 'win32':
        w.region_btn = QPushButton('▢\n\nNahrát výseč obrazovky\n\nOznačit oblast tažením myši')
        w.region_btn.setObjectName('recordOption')
        w.region_btn.setCheckable(True)
        w.region_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        w.region_btn.setMinimumHeight(245)
        w.region_btn.clicked.connect(lambda: w.select_record_mode('region'))
    else:
        w.region_btn = QPushButton('▢\n\nNahrát výseč obrazovky\n\nDostupné ve Windows')
        w.region_btn.setObjectName('recordOption')
        w.region_btn.setEnabled(False)
    w.region_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    options.addWidget(w.region_btn, 1)
    l.addLayout(options)
    choices = row(20)
    fps_frame = panel()
    fps_l = col(9)
    fps_l.setContentsMargins(17, 13, 17, 13)
    fps_frame.setLayout(fps_l)
    fps_l.addWidget(label('Snímková frekvence', 'caption'))
    w.fps_spin = QSpinBox()
    w.fps_spin.setObjectName('fpsControl')
    w.fps_spin.setRange(1, 30)
    w.fps_spin.setValue(12)
    w.fps_spin.setSuffix(' FPS')
    w.fps_spin.setMinimumWidth(112)
    w.fps_spin.setMinimumHeight(40)
    fps_l.addWidget(w.fps_spin)
    choices.addWidget(fps_frame, 1)
    length_frame = panel()
    length_l = col(9)
    length_l.setContentsMargins(17, 13, 17, 13)
    length_frame.setLayout(length_l)
    length_l.addWidget(label('Délka nahrávání', 'caption'))
    length_l.addWidget(label('Ruční zastavení', 'sectionHeading'))
    choices.addWidget(length_frame, 1)
    l.addLayout(choices)
    l.addSpacing(13)
    rec_row = row()
    rec_row.addStretch(1)
    w.rec_btn = button('◉  Spustit nahrávání', 'accent', 58)
    w.rec_btn.setObjectName('recordCTA')
    w.rec_btn.setMinimumWidth(375)
    w.rec_btn.clicked.connect(w.start_selected_recording)
    rec_row.addWidget(w.rec_btn, 3)
    rec_row.addStretch(1)
    l.addLayout(rec_row)
    l.addStretch()
    w.pages.addWidget(page)


def _make_editor_page(w):
    page = QWidget()
    l = col(17)
    l.setContentsMargins(25, 25, 25, 21)
    page.setLayout(l)
    # Navigation and export top strip.
    head = row(11)
    back = button('←', size=44)
    back.setFixedWidth(47)
    back.clicked.connect(lambda: w.show_page(0))
    head.addWidget(back)
    w.file_label = pill('Bez souboru')
    w.file_label.setMinimumWidth(185)
    head.addWidget(w.file_label)
    w.open_btn = button('↗  Otevřít GIF', size=44)
    w.open_btn.clicked.connect(w.open_dialog)
    head.addWidget(w.open_btn)
    head.addStretch()
    w.undo_top_btn = button('↶  Zrušit změny', size=44)
    w.undo_top_btn.clicked.connect(w.undo)
    head.addWidget(w.undo_top_btn)
    w.save_btn = button('↓  Uložit GIF', 'accent', 44)
    w.save_btn.setObjectName('saveCTA')
    w.save_btn.clicked.connect(w.export_dialog)
    head.addWidget(w.save_btn)
    l.addLayout(head)

    center = row(19)
    left = panel()
    left_l = col(8)
    left_l.setContentsMargins(13, 13, 13, 13)
    left.setLayout(left_l)
    left_l.addWidget(label('NÁHLED ANIMACE', 'menuTitle'))
    w.stage = Stage()
    w.stage.setMinimumSize(340, 225)
    left_l.addWidget(w.stage, 1)
    transport = row(5)
    w.first_btn = button('Ⅰ◀', 'neutral', 35)
    w.prev_btn = button('◀', 'neutral', 35)
    w.play_btn = button('▶  Přehrát', 'accent', 35)
    w.stop_btn = button('■', 'neutral', 35)
    w.next_btn = button('▶Ⅰ', 'neutral', 35)
    w.last_btn = button('▶ⅠⅠ', 'neutral', 35)
    w.first_btn.clicked.connect(lambda: w.seek(0))
    w.prev_btn.clicked.connect(lambda: w.seek(w.index - 1))
    w.play_btn.clicked.connect(w.toggle_play)
    w.stop_btn.clicked.connect(w.stop_playback)
    w.next_btn.clicked.connect(lambda: w.seek(w.index + 1))
    w.last_btn.clicked.connect(lambda: w.seek(w.project.count - 1 if w.project else 0))
    for x in [w.first_btn, w.prev_btn, w.play_btn, w.stop_btn, w.next_btn, w.last_btn]:
        transport.addWidget(x)
    transport.addStretch()
    w.time_label = label('00:00.000 / 00:00.000', 'timeText')
    transport.addWidget(w.time_label)
    left_l.addLayout(transport)
    center.addWidget(left, 7)

    right = panel()
    right.setMinimumWidth(340)
    right.setMaximumWidth(395)
    right_l = col(0)
    right_l.setContentsMargins(13, 11, 13, 11)
    right.setLayout(right_l)
    tabs = row(3)
    w.inspector_tabs = []
    w.inspector_pages = QStackedWidget()
    for ix, (symbol, title) in enumerate([('✂', 'Úsek'), ('↤', 'Rychlý střih'), ('↶', 'Historie')]):
        b = QPushButton(symbol + '\n' + title)
        b.setObjectName('tab')
        b.setCheckable(True)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setMinimumHeight(74)
        b.clicked.connect(lambda _=False, i=ix: w.show_inspector_tab(i))
        tabs.addWidget(b, 1)
        w.inspector_tabs.append(b)
    right_l.addLayout(tabs)
    w.inspector_scroll = QScrollArea()
    w.inspector_scroll.setWidgetResizable(True)
    w.inspector_scroll.setFrameShape(QFrame.Shape.NoFrame)
    w.inspector_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    w.inspector_section = QWidget()
    w.inspector_section.setObjectName('inspectorContent')
    scroll_content = col(7)
    scroll_content.setContentsMargins(11, 16, 17, 14)
    w.inspector_section.setLayout(scroll_content)
    scroll_content.addWidget(w.inspector_pages, 1)
    w.inspector_scroll.setWidget(w.inspector_section)
    right_l.addWidget(w.inspector_scroll, 1)
    _editor_trim_panel(w)
    _editor_quick_panel(w)
    _editor_history_panel(w)
    w.show_inspector_tab(0)
    center.addWidget(right, 4)
    l.addLayout(center, 1)

    timeline_panel = panel()
    t = col(8)
    t.setContentsMargins(16, 12, 16, 12)
    timeline_panel.setLayout(t)
    time_top = row(8)
    time_top.addWidget(label('ČASOVÁ OSA  /  VÝBĚR', 'menuTitle'))
    time_top.addStretch()
    time_top.addLayout(trim_unit_buttons(w, 'timeline'))
    w.frame_count_label = pill('0 SNÍMKŮ')
    time_top.addWidget(w.frame_count_label)
    t.addLayout(time_top)
    w.timeline = Timeline()
    w.timeline.setMinimumHeight(155)
    w.timeline.setMaximumHeight(170)
    w.timeline.seek.connect(w.seek)
    w.timeline.set_in.connect(w.change_mark_in)
    w.timeline.set_out.connect(w.change_mark_out)
    t.addWidget(w.timeline)
    l.addWidget(timeline_panel)
    w.pages.addWidget(page)


def _editor_trim_panel(w):
    p = QWidget()
    sc = col(11)
    sc.setContentsMargins(0, 5, 0, 5)
    p.setLayout(sc)
    sc.addWidget(label('Výběr úseku', 'sectionHeading'))
    sc.addWidget(label('Přetáhněte fialové úchyty na časové ose nebo zadejte OD / DO.', 'body', True))
    sc.addSpacing(4)
    sc.addLayout(trim_unit_buttons(w, 'trim'))
    sc.addWidget(tag('ROZSAH  ·  výběr včetně krajních snímků'))

    fields = row(12)
    fields.setContentsMargins(4, 5, 4, 5)
    one = col(7)
    one.addWidget(tag('ZAČÁTEK  /  OD'))
    w.start_value_stack = QStackedWidget()
    w.in_spin = QSpinBox()
    w.in_spin.setMinimum(1)
    w.in_spin.setMinimumHeight(42)
    w.in_spin.setToolTip('Číslo prvního zahrnutého snímku (od 1).')
    w.in_time = QTimeEdit()
    w.in_time.setDisplayFormat('HH:mm:ss.zzz')
    w.in_time.setMinimumHeight(42)
    w.in_time.setToolTip('Zadejte čas a stiskněte Enter; výběr se přichytí na celý snímek.')
    w.start_value_stack.addWidget(w.in_spin)
    w.start_value_stack.addWidget(w.in_time)
    one.addWidget(w.start_value_stack)
    fields.addLayout(one, 1)

    two = col(7)
    two.addWidget(tag('KONEC  /  DO'))
    w.end_value_stack = QStackedWidget()
    w.out_spin = QSpinBox()
    w.out_spin.setMinimum(1)
    w.out_spin.setMinimumHeight(42)
    w.out_spin.setToolTip('Číslo posledního zahrnutého snímku (od 1).')
    w.out_time = QTimeEdit()
    w.out_time.setDisplayFormat('HH:mm:ss.zzz')
    w.out_time.setMinimumHeight(42)
    w.out_time.setToolTip('Zadejte koncový čas a stiskněte Enter (konec je za posledním vybraným snímkem).')
    w.end_value_stack.addWidget(w.out_spin)
    w.end_value_stack.addWidget(w.out_time)
    two.addWidget(w.end_value_stack)
    fields.addLayout(two, 1)
    sc.addLayout(fields)

    w.in_spin.valueChanged.connect(lambda v: w.change_mark_in(v - 1))
    w.out_spin.valueChanged.connect(lambda v: w.change_mark_out(v - 1))
    # Commit time edits after Enter/focus loss; do NOT snap after each digit,
    # otherwise a user cannot finish typing a timestamp.
    w.in_time.editingFinished.connect(lambda: w._edit_start_time(w.in_time.time()))
    w.out_time.editingFinished.connect(lambda: w._edit_end_time(w.out_time.time()))

    marks = row(9)
    w.mark_in_btn = button('↤  OD = aktuální snímek', size=40)
    w.mark_out_btn = button('DO = aktuální snímek  ↦', size=40)
    w.mark_in_btn.clicked.connect(lambda: w.change_mark_in(w.index))
    w.mark_out_btn.clicked.connect(lambda: w.change_mark_out(w.index))
    marks.addWidget(w.mark_in_btn, 1)
    marks.addWidget(w.mark_out_btn, 1)
    sc.addLayout(marks)

    w.selection_summary = label('Tažením úchytů vyberte oblast střihu', 'selectionSummary', True)
    sc.addWidget(w.selection_summary)
    w.cut_btn = button('✂  Odstranit vybraný úsek', 'danger', 46)
    w.cut_btn.setToolTip('Vymaže výběr a spojí snímky vlevo a vpravo.')
    w.cut_btn.clicked.connect(w.cut_range)
    sc.addWidget(w.cut_btn)
    w.keep_btn = button('▣  Ponechat pouze výběr', 'accent', 46)
    w.keep_btn.setToolTip('Odstraní vše před výběrem i za ním; jeden krok historie.')
    w.keep_btn.clicked.connect(w.keep_selected_range)
    sc.addWidget(w.keep_btn)
    sc.addWidget(label('Čas potvrďte Enterem. Výběr se přichytí na hranice celých GIF snímků.', 'hint', True))
    sc.addStretch(1)
    w.inspector_pages.addWidget(p)

def _editor_quick_panel(w):
    p = QWidget()
    sc = col(13)
    sc.setContentsMargins(0, 5, 0, 5)
    p.setLayout(sc)
    sc.addWidget(label('Rychlý střih', 'sectionHeading'))
    sc.addWidget(label('Přejděte na konkrétní snímek a odstraňte vše před ním nebo za ním.', 'body', True))
    sc.addSpacing(12)
    w.trim_before = button('↤  Odstranit vše před snímkem', size=48)
    w.trim_after = button('Odstranit vše za snímkem  ↦', size=48)
    w.trim_before.clicked.connect(w.cut_before)
    w.trim_after.clicked.connect(w.cut_after)
    sc.addWidget(w.trim_before)
    sc.addWidget(w.trim_after)
    sc.addStretch(1)
    w.inspector_pages.addWidget(p)


def _editor_history_panel(w):
    p = QWidget()
    sc = col(13)
    sc.setContentsMargins(0, 5, 0, 5)
    p.setLayout(sc)
    sc.addWidget(label('Historie úprav', 'sectionHeading'))
    sc.addWidget(label('Vraťte provedený střih nebo obnovte původní GIF.', 'body', True))
    sc.addSpacing(12)
    r = row(10)
    w.undo_btn = button('↶  Zpět', size=46)
    w.redo_btn = button('↷  Znovu', size=46)
    w.undo_btn.clicked.connect(w.undo)
    w.redo_btn.clicked.connect(w.redo)
    r.addWidget(w.undo_btn)
    r.addWidget(w.redo_btn)
    sc.addLayout(r)
    w.reset_btn = button('⟳  Obnovit originál', size=46)
    w.reset_btn.clicked.connect(w.reset)
    sc.addWidget(w.reset_btn)
    sc.addStretch(1)
    w.inspector_pages.addWidget(p)


def _make_library_page(w):
    page = QWidget()
    l = col(19)
    l.setContentsMargins(50, 45, 50, 30)
    page.setLayout(l)
    l.addWidget(label('Moje GIFy', 'heading'))
    l.addWidget(label('Otevřete GIF z počítače a upravujte ho snímek po snímku.', 'body'))
    l.addSpacing(18)
    r = row(14)
    open_gif = button('↗  Otevřít GIF ze souboru', 'accent', 55)
    open_gif.clicked.connect(w.open_dialog)
    r.addWidget(open_gif)
    r.addStretch()
    l.addLayout(r)
    info = panel()
    info_l = col(15)
    info_l.setContentsMargins(24, 24, 24, 24)
    info.setLayout(info_l)
    info_l.addWidget(label('Naposledy otevřený GIF', 'sectionHeading'))
    w.library_item = button('Zatím nebyl otevřen žádný GIF', size=54)
    w.library_item.clicked.connect(w.open_recent_gif)
    w.library_item.setEnabled(False)
    info_l.addWidget(w.library_item)
    l.addWidget(info)
    l.addStretch()
    w.pages.addWidget(page)


def _make_settings_page(w):
    page = QWidget()
    l = col(20)
    l.setContentsMargins(50, 44, 50, 34)
    page.setLayout(l)
    l.addWidget(label('Nastavení', 'heading'))
    l.addWidget(label('Vzhled aplikace a ovládání. Nahrávací backend se nemění.', 'body'))
    theme_box = panel()
    theme_l = row(16)
    theme_l.setContentsMargins(23, 22, 23, 22)
    theme_box.setLayout(theme_l)
    text_group = col(8)
    text_group.addWidget(label('Barevný motiv', 'sectionHeading'))
    text_group.addWidget(label('Přepínat můžete také klávesovou zkratkou Ctrl+L.', 'body'))
    theme_l.addLayout(text_group, 1)
    w.settings_theme_btn = button('Přepnout motiv', size=45)
    w.settings_theme_btn.clicked.connect(w.toggle_theme)
    theme_l.addWidget(w.settings_theme_btn)
    l.addWidget(theme_box)
    l.addWidget(label('TIP: Ctrl+O otevře GIF, Ctrl+S uloží, Ctrl+Z vrátí poslední střih.', 'body', True))
    l.addStretch()
    w.pages.addWidget(page)


def apply_modern_theme(w):
    c = COLORS[w.theme]
    w.setStyleSheet(modern_stylesheet(w.theme))
    w.theme_btn.setText('☾  Tmavý režim' if w.theme == 'light' else '☀  Světlý režim')
    w.settings_theme_btn.setText('☾  Tmavý režim' if w.theme == 'light' else '☀  Světlý režim')
    w.timeline.set_theme(w.theme)
    w.inspector_section.setStyleSheet('background:transparent;border:none;')
    w.inspector_scroll.viewport().setStyleSheet('background:transparent;border:none;')
    for ctrl, role in [
        (w.mark_in_btn, 'mark_in'), (w.mark_out_btn, 'mark_out'),
        (w.cut_btn, 'cut'), (w.trim_before, 'trim'), (w.trim_after, 'trim'),
        (w.undo_btn, 'history'), (w.redo_btn, 'history'),
        (w.reset_btn, 'reset'),
    ]:
        ctrl.setStyleSheet(inspector_action_style(w.theme, role))
    w.in_spin.setStyleSheet(inspector_field_style(w.theme, 'mark_in'))
    w.out_spin.setStyleSheet(inspector_field_style(w.theme, 'mark_out'))
    w.in_time.setStyleSheet(inspector_field_style(w.theme, 'mark_in').replace('QSpinBox', 'QTimeEdit'))
    w.out_time.setStyleSheet(inspector_field_style(w.theme, 'mark_out').replace('QSpinBox', 'QTimeEdit'))
    w.fps_spin.setStyleSheet('''QSpinBox {color:%s;background:%s;border:2px solid %s;
        border-radius:11px;padding:9px 11px;font-size:14px;font-weight:750;}
        QSpinBox::up-button,QSpinBox::down-button {width:18px;border:none;}'''
        % (c['text'], c['input'], c['accent']))
    if w.capture_bar:
        w.capture_bar.apply_theme(w.theme)
    w.update()
