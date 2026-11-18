"""v3.2 visual regression checks (do not depend on a display)."""
from pathlib import Path
from modern_theme import COLORS, modern_stylesheet
from theme import contrast_ratio

ROOT = Path(__file__).resolve().parent.parent
UI = (ROOT / 'modern_ui.py').read_text(encoding='utf-8')
APP = (ROOT / 'app.py').read_text(encoding='utf-8')


def test_marker_fields_have_explicit_outside_and_inside_gutters():
    assert 'sc.setContentsMargins(0, 5, 0, 5)' in UI
    assert 'fields.setContentsMargins(2, 7, 2, 6)' in UI
    assert 'one = col(8)' in UI
    assert 'two = col(8)' in UI


def test_fps_input_is_visible_and_styled():
    assert "w.fps_spin.setObjectName('fpsControl')" in UI
    assert 'w.fps_spin.setMinimumWidth(112)' in UI
    assert 'border:2px solid' in UI
    for mode in ('dark', 'light'):
        c = COLORS[mode]
        assert contrast_ratio(c['text'], c['input']) >= 4.5


def test_theme_in_footer_and_sidebar_present():
    assert 'foot.addWidget(w.theme_btn)' in UI
    assert "'Ctrl+L':self.toggle_theme" in APP
    assert "'▣   Nahrávání'" in UI
    assert "'✂   Upravit GIF'" in UI
    assert "'▤   Moje GIFy'" in UI
    assert "'⚙   Nastavení'" in UI
    assert 'w.pages = QStackedWidget()' in UI


def test_contrast_in_two_distinct_themes():
    assert COLORS['dark']['bg'] != COLORS['light']['bg']
    assert 'QPushButton#recordOption:checked' in modern_stylesheet('dark')
    assert 'QPushButton#tab:checked' in modern_stylesheet('dark')
    for mode in ('dark', 'light'):
        c = COLORS[mode]
        assert contrast_ratio(c['text'], c['surface']) >= 4.5
        assert contrast_ratio(c['sub'], c['surface']) >= 4.5
