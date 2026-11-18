"""Appearance palettes for GIFRipper; deliberately independent of capture code."""

PALETTES = {
    'dark': dict(
        text='#F4F7FF', muted='#B6C6DC', bg='#192339', card='rgba(23,29,49,232)',
        border='#465673', btn='#293A55', hover='#3A4F70', btn_text='#F3F7FF',
        disabled_bg='#253249', disabled_text='#B4C3D7', disabled_border='#50617C',
        input='#101B2C', pill='#2B3C55', pill_text='#E6F0FC',
        danger='#512839', danger_hover='#79384F', danger_text='#FFD4DF',
        danger_disabled='#3D303C', danger_disabled_text='#C3ABBA',
        start='#C4FF28', end='#FFAFC1', logo='#F5F7FF', logo_green='#C4FF28',
        accent='#C4FF28', accent_hover='#DCFF80',
        banner='#27362B', banner_text='#E8FFD0',
    ),
    'light': dict(
        text='#132740', muted='#455D7A', bg='#EEF3FB', card='rgba(251,253,255,248)',
        border='#B8C9DD', btn='#DDE8F7', hover='#C5D7EC', btn_text='#193350',
        disabled_bg='#E6ECF4', disabled_text='#566A80', disabled_border='#C0CCDA',
        input='#FFFFFF', pill='#DFEAF8', pill_text='#2A4566',
        danger='#FBE2E9', danger_hover='#F5C4D1', danger_text='#8D2444',
        danger_disabled='#F4E8EE', danger_disabled_text='#936A7D',
        start='#4C7300', end='#AA3059', logo='#132740', logo_green='#587E00',
        accent='#B2E526', accent_hover='#C6F454',
        banner='#E7F5D1', banner_text='#29470D',
    ),
}


def stylesheet(theme: str) -> str:
    c = PALETTES.get(theme, PALETTES['dark'])
    return '''
* {font-family:"Inter", "Segoe UI", "Arial"; color:%(text)s;}
QFrame#glass {background:%(card)s; border:1px solid %(border)s; border-radius:24px;}
QPushButton {color:%(btn_text)s; background:%(btn)s; border:1px solid %(border)s;
  border-radius:12px; font-weight:650; padding:8px 14px; font-size:12px;}
QPushButton:hover {background:%(hover)s;}
QPushButton:pressed {background:%(hover)s;}
QPushButton:disabled {color:%(disabled_text)s; background:%(disabled_bg)s; border-color:%(disabled_border)s;}
QPushButton#accent {color:#152300; background:%(accent)s; border-color:%(accent)s; font-weight:800;}
QPushButton#accent:hover {background:%(accent_hover)s;}
QPushButton#accent:disabled {color:%(disabled_text)s; background:%(disabled_bg)s; border-color:%(disabled_border)s;}
QPushButton#danger, QPushButton#inspectorDanger {color:%(danger_text)s; background:%(danger)s;
  border:1px solid %(danger_text)s; font-weight:800;}
QPushButton#danger:hover, QPushButton#inspectorDanger:hover {background:%(danger_hover)s;}
QPushButton#danger:disabled, QPushButton#inspectorDanger:disabled {color:%(danger_disabled_text)s;
  background:%(danger_disabled)s; border-color:%(disabled_border)s;}
QPushButton#inspectorAction {color:%(btn_text)s; background:%(btn)s;
  border:1px solid %(border)s; font-weight:750;}
QPushButton#inspectorAction:hover {background:%(hover)s;}
QPushButton#inspectorAction:disabled {color:%(disabled_text)s; background:%(disabled_bg)s;
  border-color:%(disabled_border)s;}
QPushButton#ghost, QPushButton#inspectorGhost {color:%(text)s; background:transparent; border:1px solid %(border)s;}
QPushButton#ghost:hover, QPushButton#inspectorGhost:hover {background:%(hover)s;}
QPushButton#ghost:disabled, QPushButton#inspectorGhost:disabled {color:%(disabled_text)s;
  background:transparent; border-color:%(disabled_border)s;}
QPushButton#themeToggle {color:%(muted)s; background:%(card)s;
  border:1px solid %(border)s; border-radius:13px; font-weight:700;
  font-size:11px; padding:6px 10px;}
QPushButton#themeToggle:hover {color:%(text)s; background:%(hover)s; border-color:%(accent)s;}
QSpinBox {background:%(input)s; border:1px solid %(border)s; border-radius:10px;
  color:%(text)s; padding:7px 10px; min-height:22px; font-size:13px;}
QSpinBox:disabled {background:%(disabled_bg)s; color:%(disabled_text)s;
  border-color:%(disabled_border)s;}
QSpinBox::up-button, QSpinBox::down-button {width:17px; border:none;}
QLabel#body {color:%(muted)s; font-size:12px;}
QLabel#subtitle {color:%(muted)s; font-size:10px; letter-spacing:2px;}
QLabel#timeText {color:%(text)s; font-size:12px; font-weight:750;}
QLabel#statusText {color:%(muted)s; font-size:11px;}
QLabel#fpsLabel {color:%(text)s; font-size:12px; font-weight:650;}
QFrame#captureBanner {background:%(banner)s; border:1px solid %(start)s; border-radius:14px;}
QLabel#bannerText {color:%(banner_text)s; font-size:13px; font-weight:700;}
QLabel#tag {color:%(muted)s; font-weight:700; letter-spacing:1px; background:transparent;}
QLabel#tag[role="start"] {color:%(start)s;}
QLabel#tag[role="end"] {color:%(end)s;}
QLabel#pill {color:%(pill_text)s; background:%(pill)s; border:1px solid %(border)s;
  border-radius:12px; padding:7px 12px; font-size:12px;}
QScrollArea {background:%(bg)s; border:none;}
QWidget#inspectorContent {background:%(bg)s; border:none;}
QScrollBar:vertical {background:transparent; width:8px;}
QScrollBar::handle:vertical {background:%(border)s; border-radius:4px; min-height:35px;}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {height:0px;}
QToolTip {color:%(text)s; background:%(card)s; border:1px solid %(border)s; padding:5px;}
''' % c


def contrast_ratio(fg: str, bg: str) -> float:
    """Accessibility regression test helper for opaque text/background swatches."""
    def luminance(col):
        vals = [int(col[i:i+2], 16) / 255 for i in (1,3,5)]
        linear = [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in vals]
        return .2126*linear[0]+.7152*linear[1]+.0722*linear[2]
    a,b = sorted([luminance(fg), luminance(bg)], reverse=True)
    return (a+.05)/(b+.05)

# Explicit local QSS for the editor controls. Qt does not always cascade a
# QMainWindow stylesheet through QScrollArea's viewport and styled content
# widget on GNOME/Wayland. Attaching these rules to the controls themselves
# keeps real borders and filled backgrounds visible on every platform.
EDITOR_BUTTONS = {
    'dark': {
        'mark_in': ('#183C5F', '#67B8FF', '#F2FAFF', '#27547D', '#192F45', '#4C789D', '#C6DFF2'),
        'mark_out': ('#312B59', '#B5A2FF', '#F5F1FF', '#483E79', '#29273F', '#7469A2', '#D8D0F3'),
        'cut': ('#67263D', '#FF6389', '#FFF0F4', '#86324F', '#432937', '#AB637E', '#F2CBD5'),
        'trim': ('#50371F', '#FFBF6B', '#FFF4E5', '#6D4A28', '#3A3025', '#96754D', '#E7D4B8'),
        'history': ('#16463F', '#6CE4C6', '#EBFFF9', '#256157', '#253A36', '#549D8C', '#C4E8DD'),
        'reset': ('#30364B', '#9DAFD5', '#F0F4FF', '#424B67', '#283044', '#687C9D', '#C5D2EA'),
    },
    'light': {
        'mark_in': ('#DAEDFF', '#2479B8', '#123D61', '#C3E1FC', '#E4EEF8', '#87B4D3', '#426F92'),
        'mark_out': ('#ECE5FF', '#7850BF', '#462B7B', '#DCCEFF', '#F0EBF8', '#AE9ACF', '#755A9D'),
        'cut': ('#FFE0E9', '#CE3764', '#841D3E', '#FFCAD9', '#F7E4EB', '#D098AD', '#8B3F5A'),
        'trim': ('#FFF0D9', '#B96C1E', '#74400B', '#FFE1B9', '#F6EBDF', '#C6A17C', '#84613E'),
        'history': ('#DDF7EF', '#198E76', '#075A49', '#C1EBDD', '#E4F1ED', '#87BBAF', '#2C6659'),
        'reset': ('#E7ECF7', '#647DA9', '#344A70', '#D8E2F3', '#E9EDF4', '#A4B2CA', '#53627A'),
    },
}


def inspector_action_style(theme: str, role: str) -> str:
    """Visible filled button with a colored outline even when disabled."""
    mode = theme if theme in EDITOR_BUTTONS else 'dark'
    bg, border, text, hover, disabled_bg, disabled_border, disabled_text = EDITOR_BUTTONS[mode][role]
    return f'''
QPushButton {{
    color: {text}; background-color: {bg};
    border: 2px solid {border}; border-radius: 12px;
    font-family: "Inter", "Segoe UI", "Arial";
    font-size: 12px; font-weight: 750; padding: 9px 9px;
}}
QPushButton:hover:!disabled {{ background-color: {hover}; border: 2px solid {border}; }}
QPushButton:pressed:!disabled {{ background-color: {hover}; padding-top: 10px; }}
QPushButton:disabled {{
    color: {disabled_text}; background-color: {disabled_bg};
    border: 2px solid {disabled_border};
}}
'''


def inspector_field_style(theme: str, role: str) -> str:
    """Explicitly style range and FPS inputs; scroll-area children cannot rely on inherited QSS."""
    mode = theme if theme in EDITOR_BUTTONS else 'dark'
    c = PALETTES[mode]
    if role == 'fps':
        # A prominent lime/green recording setting that reads as a real input.
        bg, border, foreground, hover, disabled_bg, disabled_border, disabled_text = {
            'dark': ('#1B342D', '#A8EE68', '#E7FFD7', '#284936', '#253A35', '#6F936B', '#D6EACA'),
            'light': ('#DBF6C6', '#4F8327', '#294B18', '#C7ECAA', '#E5F0DF', '#9DB88D', '#4A6942'),
        }[mode]
    else:
        _, border, _, _, _, disabled_border, disabled_text = EDITOR_BUTTONS[mode][role]
        bg, foreground, hover, disabled_bg = c['input'], c['text'], c['btn'], c['disabled_bg']
    return f'''
QSpinBox {{
    background-color: {bg}; color: {foreground};
    border: 2px solid {border}; border-radius: 11px;
    padding: 7px 10px; min-height: 24px; font-size: 13px; font-weight: 750;
}}
QSpinBox:hover:!disabled, QSpinBox:focus {{
    background-color: {hover}; border: 2px solid {border};
}}
QSpinBox:disabled {{
    background-color: {disabled_bg}; color: {disabled_text};
    border: 2px solid {disabled_border};
}}
QSpinBox::up-button, QSpinBox::down-button {{
    width: 16px; border: none; background: transparent;
}}
'''
