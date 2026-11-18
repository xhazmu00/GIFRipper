"""No-Qt regressions: editor buttons must be visually bounded and distinct."""
from theme import EDITOR_BUTTONS, inspector_action_style, inspector_field_style, contrast_ratio


def test_all_editor_action_buttons_have_real_filled_border_in_every_state():
    for mode in ('dark', 'light'):
        for role in ('mark_in', 'mark_out', 'cut', 'trim', 'history', 'reset'):
            css = inspector_action_style(mode, role)
            assert 'border: 2px solid' in css
            assert 'background-color:' in css
            assert 'QPushButton:hover:!disabled' in css
            assert 'QPushButton:disabled' in css
            bg, border, text, hover, disabled_bg, disabled_border, disabled_text = EDITOR_BUTTONS[mode][role]
            assert bg != disabled_bg != hover
            assert border != disabled_border
            assert contrast_ratio(text, bg) >= 4.5, (mode, role, 'normal contrast')
            assert contrast_ratio(disabled_text, disabled_bg) >= 4.5, (mode, role, 'disabled contrast')


def test_roles_are_distinct():
    for mode in ('dark', 'light'):
        colors = [EDITOR_BUTTONS[mode][role][0] for role in ('mark_in', 'mark_out', 'cut', 'trim', 'history')]
        assert len(set(colors)) == len(colors)


def test_marker_spins_have_matching_colored_outline():
    for mode in ('dark', 'light'):
        for role in ('mark_in', 'mark_out'):
            css = inspector_field_style(mode, role)
            assert 'border: 2px solid' in css
            assert EDITOR_BUTTONS[mode][role][1] in css
            assert 'QSpinBox:disabled' in css
