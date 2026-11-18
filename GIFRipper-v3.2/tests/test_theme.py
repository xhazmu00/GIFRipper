"""Theme regression tests work without a display or Qt installation."""
from theme import PALETTES, contrast_ratio, stylesheet


def test_stylesheet_contains_theming_and_editor_controls():
    for mode in ('light', 'dark'):
        css = stylesheet(mode)
        assert 'QPushButton#inspectorAction:disabled' in css
        assert 'QPushButton#inspectorDanger:disabled' in css
        assert 'QPushButton#themeToggle' in css
        assert 'QWidget#inspectorContent' in css
        assert PALETTES[mode]['btn_text'] in css
        assert PALETTES[mode]['bg'] in css


def test_text_buttons_reach_minimum_wcag_aa_contrast():
    for c in PALETTES.values():
        assert contrast_ratio(c['btn_text'], c['btn']) >= 4.5
        assert contrast_ratio(c['disabled_text'], c['disabled_bg']) >= 4.5
        assert contrast_ratio(c['danger_text'], c['danger']) >= 4.5
        assert contrast_ratio(c['text'], c['input']) >= 4.5


def test_light_and_dark_have_distinct_inspector_styles():
    assert PALETTES['light']['bg'] != PALETTES['dark']['bg']
    assert stylesheet('dark') != stylesheet('light')


def test_unknown_theme_falls_back_to_dark():
    assert stylesheet('???') == stylesheet('dark')
