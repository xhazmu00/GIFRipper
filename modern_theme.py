"""GIFRipper 3.2: presentation-only QSS, inspired by the supplied purple mockups.

No capture, processing or filesystem APIs belong in this module.
"""


COLORS = {
    'dark': {
        'bg': '#0D0E17', 'surface': '#151622', 'surface2': '#1A1B29',
        'surface3': '#232337', 'sidebar': '#161723', 'border': '#303044',
        'text': '#FAF9FF', 'sub': '#B9B7C9', 'muted': '#8A8B9F',
        'accent': '#A85BFF', 'accent2': '#813DF1', 'on_accent': '#FFFFFF',
        'input': '#222336', 'hover': '#2B2A43', 'hover_border': '#7956B7',
        'disabled': '#383749', 'disabled_text': '#A7A4BB',
    },
    'light': {
        'bg': '#F2F0FA', 'surface': '#FFFFFF', 'surface2': '#F9F7FD',
        'surface3': '#EEE8FA', 'sidebar': '#FBF9FF', 'border': '#D9D2E8',
        'text': '#221934', 'sub': '#5C526D', 'muted': '#746985',
        'accent': '#7733DA', 'accent2': '#9352EE', 'on_accent': '#FFFFFF',
        'input': '#F8F6FC', 'hover': '#EBE2FB', 'hover_border': '#A377E1',
        'disabled': '#EAE5F0', 'disabled_text': '#6A6178',
    },
}


def modern_stylesheet(theme: str) -> str:
    c = COLORS.get(theme, COLORS['dark'])
    return '''
* { font-family: "Inter", "Segoe UI", "Arial"; color: %(text)s; }
QWidget#shell {background:%(bg)s;}
QFrame#sidebar {background:%(sidebar)s; border-right:1px solid %(border)s;}
QFrame#topBrand {background:transparent; border-bottom:1px solid %(border)s;}
QFrame#panel, QFrame#glass {background:%(surface)s; border:1px solid %(border)s; border-radius:19px;}
QFrame#optionCard {background:%(surface2)s; border:2px solid %(border)s; border-radius:22px;}
QFrame#settingsCard {background:%(surface)s; border:1px solid %(border)s; border-radius:18px;}
QLabel {background:transparent;}
QLabel#brand {font-size:23px; font-weight:850; color:%(text)s;}
QLabel#heading {font-size:31px; font-weight:850; color:%(text)s;}
QLabel#sectionHeading {font-size:18px; font-weight:800; color:%(text)s;}
QLabel#body {font-size:13px; color:%(sub)s;}
QLabel#small {font-size:11px; color:%(muted)s;}
QLabel#caption {font-size:12px; color:%(sub)s;}
QLabel#fileTitle {font-size:18px; font-weight:800;}
QLabel#menuTitle {font-size:12px; color:%(muted)s; letter-spacing:1px;}
QLabel#statusText {font-size:11px; color:%(sub)s;}
QLabel#timeText {font-size:13px; color:%(sub)s; font-weight:700;}
QLabel#fpsLabel {font-size:12px; color:%(sub)s; font-weight:650;}
QLabel#tag {font-size:11px; color:%(sub)s; font-weight:750; letter-spacing:0px;}
QLabel#tag[role="start"] {color:%(accent)s;}
QLabel#tag[role="end"] {color:%(sub)s;}
QLabel#pill {background:%(surface3)s; color:%(sub)s; border:1px solid %(border)s;
 border-radius:13px; padding:6px 12px; font-size:11px;}
QPushButton {background:%(surface3)s; border:1px solid %(border)s;
 border-radius:12px; padding:10px 14px; font-size:13px; font-weight:650; color:%(text)s;}
QPushButton:hover:!disabled {background:%(hover)s; border:1px solid %(hover_border)s;}
QPushButton:pressed:!disabled {background:%(surface3)s;}
QPushButton:disabled {background:%(disabled)s; color:%(disabled_text)s; border-color:%(border)s;}
QPushButton#accent, QPushButton#recordCTA, QPushButton#saveCTA {
 color:%(on_accent)s; background:%(accent2)s; border:1px solid %(accent)s;
 font-size:14px; font-weight:800; border-radius:14px;}
QPushButton#accent:hover:!disabled, QPushButton#recordCTA:hover:!disabled,
QPushButton#saveCTA:hover:!disabled {background:%(accent)s;}
QPushButton#navButton {background:transparent; border:1px solid transparent;
 border-radius:11px; text-align:left; padding:14px 17px; color:%(sub)s; font-size:14px;}
QPushButton#navButton:hover {background:%(hover)s; color:%(text)s;}
QPushButton#navButton:checked {background:%(surface3)s; border:1px solid %(hover_border)s;
 color:%(accent)s; font-weight:750;}
QPushButton#recordOption {background:%(surface2)s; border:2px solid %(border)s;
 border-radius:21px; text-align:center; font-size:16px; font-weight:750;
 padding:18px; color:%(text)s;}
QPushButton#recordOption:hover:!disabled {background:%(hover)s; border:2px solid %(hover_border)s;}
QPushButton#recordOption:checked {background:%(surface3)s; border:2px solid %(accent)s;}
QPushButton#recordOption:disabled {background:%(surface2)s; border:2px solid %(border)s;
 color:%(muted)s;}
QPushButton#tab {background:transparent; border:none; border-bottom:3px solid transparent;
 border-radius:0; padding:14px 10px; font-size:12px; color:%(sub)s;}
QPushButton#tab:checked {background:%(surface3)s; color:%(accent)s; border-bottom:3px solid %(accent)s;}
QPushButton#tab:hover {background:%(hover)s;}
QPushButton#danger {background:#4C243C; border:1px solid #E36AA1; color:#FFDBED; font-weight:700;}
QPushButton#danger:hover {background:#6B2B4E;}
QPushButton#themeToggle {padding:7px 13px; font-size:12px;}
QPushButton#unitToggle {background:%(input)s; border:1px solid %(border)s;
 border-radius:9px; padding:6px 9px; font-size:12px; font-weight:750; color:%(sub)s;}
QPushButton#unitToggle:hover {border-color:%(accent)s; color:%(text)s;}
QPushButton#unitToggle:checked {background:%(surface3)s; color:%(accent)s;
 border:2px solid %(accent)s;}
QLabel#selectionSummary {background:%(surface3)s; border:1px solid %(border)s;
 border-radius:8px; padding:8px 10px; color:%(text)s; font-size:11px; font-weight:750;}
QLabel#hint {font-size:11px; color:%(muted)s; line-height:1.25;}
QSpinBox, QTimeEdit, QComboBox {background:%(input)s; border:1px solid %(border)s; border-radius:11px;
 padding:8px 10px; font-size:13px; color:%(text)s; min-height:28px;}
QSpinBox:hover, QTimeEdit:hover, QComboBox:hover {border:1px solid %(accent)s;}
QSpinBox::up-button, QSpinBox::down-button, QTimeEdit::up-button, QTimeEdit::down-button {width:17px; border:none; background:transparent;}
QScrollArea, QScrollArea>QWidget>QWidget {background:transparent; border:none;}
QWidget#inspectorContent {background:transparent; border:none;}
QFrame#captureBanner {background:%(surface3)s; border:1px solid %(accent)s; border-radius:13px;}
QLabel#bannerText {color:%(text)s; font-size:12px; font-weight:700;}
QScrollBar:vertical {background:transparent; width:7px;}
QScrollBar::handle:vertical {background:%(border)s; border-radius:3px; min-height:35px;}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {height:0px;}
QToolTip {background:%(surface)s; color:%(text)s; border:1px solid %(accent)s; padding:6px;}
''' % c
