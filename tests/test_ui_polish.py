"""UI-polish regression checks that don't require Qt on CI/headless machines."""
from pathlib import Path

from theme import PALETTES, contrast_ratio, inspector_field_style


APP = (Path(__file__).parent.parent / 'app.py').read_text(encoding='utf-8')


def test_marker_fields_have_explicit_outside_and_inside_gutters():
    assert 'sc.setContentsMargins(11, 10, 15, 8)' in APP
    assert 'line.setContentsMargins(2, 7, 2, 6)' in APP
    assert 'one.setSpacing(8)' in APP
    assert 'two.setSpacing(8)' in APP


def test_fps_spin_is_a_styled_control_with_room_for_its_value():
    assert "self.fps_spin.setObjectName('fpsControl')" in APP
    assert 'self.fps_spin.setMinimumWidth(112)' in APP
    assert "self.fps_spin.setStyleSheet(inspector_field_style(self.theme, 'fps'))" in APP
    for mode in ('dark', 'light'):
        qss = inspector_field_style(mode, 'fps')
        assert 'border: 2px solid' in qss
        assert 'background-color:' in qss
        assert 'QSpinBox:hover' in qss
    # Explicit palette swatches remain readable on both backgrounds.
    assert contrast_ratio('#E7FFD7', '#1B342D') > 4.5
    assert contrast_ratio('#294B18', '#DBF6C6') > 4.5


def test_platform_specific_instructions_are_not_part_of_recording_panel():
    assert 'Linux Wayland: systémové okno' not in APP
    assert 'Potom vybereš oblast tažením myši.' not in APP


def test_theme_is_in_footer_not_main_toolbar():
    header_start = APP.index('header = QHBoxLayout()')
    header_end = APP.index('root.addLayout(header)')
    assert 'theme_btn' not in APP[header_start:header_end]
    footer_start = APP.index('status = QHBoxLayout()')
    footer_end = APP.index('root.addLayout(status)')
    assert 'status.addWidget(self.theme_btn)' in APP[footer_start:footer_end]
    assert "'Ctrl+L':self.toggle_theme" in APP


def test_themes_still_have_distinct_accessible_text_colors():
    assert PALETTES['dark']['bg'] != PALETTES['light']['bg']
    for mode in ('dark', 'light'):
        c = PALETTES[mode]
        assert contrast_ratio(c['text'], c['input']) >= 4.5
