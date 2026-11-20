"""Regras dos atalhos de teclado, sem display."""

import pytest

from pomodoro.ui.shortcuts import (
    HINT_TEXT,
    STATE_CONTROL,
    ShortcutAction,
    shortcut_action,
)


@pytest.mark.parametrize(
    ("keysym", "action"),
    [
        ("space", ShortcutAction.TOGGLE),
        ("r", ShortcutAction.RESET),
        ("R", ShortcutAction.RESET),
        ("s", ShortcutAction.SKIP),
        ("S", ShortcutAction.SKIP),
    ],
)
def test_keys_map_to_actions(keysym, action):
    assert shortcut_action(keysym) is action


@pytest.mark.parametrize("keysym", ["a", "Return", "Escape", "p", "x", "1", "Tab"])
def test_other_keys_do_nothing(keysym):
    assert shortcut_action(keysym) is None


@pytest.mark.parametrize("widget_class", ["Entry", "TEntry", "Text", "Spinbox", "TCombobox"])
def test_ignored_in_text_fields(widget_class):
    assert shortcut_action("space", widget_class=widget_class) is None
    assert shortcut_action("r", widget_class=widget_class) is None
    assert shortcut_action("s", widget_class=widget_class) is None


@pytest.mark.parametrize("widget_class", ["Canvas", "Frame", "Label", "Tk", "CTk", ""])
def test_works_on_non_text_widgets(widget_class):
    assert shortcut_action("space", widget_class=widget_class) is ShortcutAction.TOGGLE


def test_ignored_outside_main_window():
    assert shortcut_action("space", in_main_window=False) is None
    assert shortcut_action("s", widget_class="Canvas", in_main_window=False) is None


def test_ignored_with_ctrl_or_alt():
    assert shortcut_action("r", state=STATE_CONTROL) is None
    assert shortcut_action("s", state=0x20000, alt_mask=0x20000) is None
    assert shortcut_action("s", state=0x8, alt_mask=0x8) is None


def test_num_lock_on_windows_does_not_block():
    # No Windows, 0x8 (Mod1) indica Num Lock; Alt é 0x20000.
    assert shortcut_action("space", state=0x8, alt_mask=0x20000) is ShortcutAction.TOGGLE


def test_shift_and_caps_lock_do_not_block():
    assert shortcut_action("R", state=0x1) is ShortcutAction.RESET  # Shift
    assert shortcut_action("S", state=0x2) is ShortcutAction.SKIP  # Caps Lock


def test_hint_mentions_every_key():
    for key in ("Espaço", "R", "S"):
        assert key in HINT_TEXT
