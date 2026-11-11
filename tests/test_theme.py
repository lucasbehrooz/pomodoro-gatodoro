"""Testes dos temas. Testes unitários não abrem janelas.

O smoke de UI (que cria janelas Tk reais) só roda com opt-in:

    POMODORO_UI_SMOKE=1 pytest tests/test_theme.py
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import fields
from pathlib import Path

import pytest

from pomodoro.config import Config, load_config, save_config
from pomodoro.storage import Storage
from pomodoro.ui.settings import SettingsError, build_config, form_values
from pomodoro.ui.stats import _DARK, _LIGHT, chart_colors
from pomodoro.ui.theme import (
    DEFAULT_THEME,
    ESCURO,
    FEMININO,
    PADRAO,
    THEME_LABELS,
    THEMES,
    Palette,
    get_palette,
    is_valid_theme,
    theme_key_from_label,
    theme_label,
)

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
COLOR_FIELDS = [f.name for f in fields(Palette) if f.name != "name"]
# Campos que o tema padrão deixa como None (usa o padrão do CustomTkinter).
DEFAULTABLE = {
    f.name
    for f in fields(Palette)
    if f.name not in ("name", "warning", "error")
}


def _luminance(hex_color: str) -> float:
    values = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _contrast(a: str, b: str) -> float:
    la, lb = sorted([_luminance(a), _luminance(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


# ---- paletas -----------------------------------------------------------------


def test_theme_keys_match_labels():
    assert set(THEMES) == set(THEME_LABELS) == {"padrao", "feminino", "escuro"}
    assert DEFAULT_THEME == "padrao"


@pytest.mark.parametrize("name", list(THEMES))
def test_every_palette_field_is_hex_or_default(name):
    palette = THEMES[name]
    assert palette.name == name
    for field in COLOR_FIELDS:
        value = getattr(palette, field)
        if value is None:
            assert name == "padrao" and field in DEFAULTABLE, (
                f"{name}.{field} sem cor; só o padrão pode usar None"
            )
        else:
            assert HEX_RE.match(value), f"{name}.{field} = {value!r} não é #RRGGBB"


def test_feminino_and_escuro_define_every_color():
    for palette in (FEMININO, ESCURO):
        for field in COLOR_FIELDS:
            assert getattr(palette, field) is not None, f"{palette.name}.{field}"


def test_padrao_keeps_ctk_defaults_except_status_colors():
    # Tema padrão não define cores de fundo/texto: herda o CustomTkinter,
    # então a aparência original não muda.
    assert all(getattr(PADRAO, f) is None for f in DEFAULTABLE)
    assert PADRAO.warning == "#f0ad4e"
    assert PADRAO.error == "#d9534f"


def test_feminino_colors_match_spec():
    assert FEMININO.bg == "#FDF0F5"
    assert FEMININO.card == "#F7E6F0"
    assert FEMININO.accent == "#E0609A"
    assert FEMININO.accent_hover == "#C94C86"
    assert FEMININO.text == "#4A1F3D"
    assert FEMININO.muted == "#8A5A78"


# ---- contraste (WCAG AA, 4.5:1 para texto) -----------------------------------


@pytest.mark.parametrize("palette", [FEMININO, ESCURO], ids=["feminino", "escuro"])
def test_text_pairs_meet_aa_contrast(palette: Palette):
    pairs = [
        (palette.text, palette.card),
        (palette.text, palette.bg),
        (palette.text, palette.entry_bg),
        (palette.muted, palette.bg),
        (palette.muted, palette.card),
        (palette.button_text, palette.accent),
        (palette.button_text, palette.accent_hover),
        (palette.error, palette.bg),
        (palette.error, palette.card),
        (palette.warning, palette.card),
    ]
    for fg, bg in pairs:
        assert _contrast(fg, bg) >= 4.5, f"{palette.name}: {fg} sobre {bg}"


# ---- get_palette e rótulos ---------------------------------------------------


@pytest.mark.parametrize("name", ["padrao", "feminino", "escuro"])
def test_get_palette_known(name):
    assert get_palette(name) is THEMES[name]


@pytest.mark.parametrize("name", ["", "rosa", "FEMININO", None, 5, ["feminino"]])
def test_get_palette_unknown_returns_padrao(name):
    assert get_palette(name) is PADRAO


def test_is_valid_theme():
    assert is_valid_theme("escuro")
    assert not is_valid_theme("azul")
    assert not is_valid_theme(None)
    assert not is_valid_theme(["escuro"])


def test_label_and_key_mapping_roundtrip():
    for key in THEMES:
        assert theme_key_from_label(theme_label(key)) == key
    assert theme_label("feminino") == "Rosa"
    assert theme_key_from_label("Escuro") == "escuro"
    assert theme_key_from_label("Padrão") == "padrao"


def test_label_mapping_unknown_values():
    assert theme_key_from_label("Rosa") is None
    assert theme_key_from_label("") is None
    assert theme_label("nao-existe") == "Padrão"


# ---- configuração ------------------------------------------------------------


def test_config_default_theme_is_padrao():
    assert Config().theme == "padrao"
    assert any(f.name == "theme" for f in fields(Config))


def test_invalid_theme_in_json_falls_back_to_padrao(tmp_path: Path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"theme": "neon", "focus_minutes": 30}), encoding="utf-8")
    cfg = load_config(path)
    assert cfg.theme == "padrao"
    assert cfg.focus_minutes == 30  # demais campos não são afetados


@pytest.mark.parametrize("value", [5, None, ["feminino"], {"a": 1}, True])
def test_non_string_theme_in_json_falls_back_to_padrao(tmp_path: Path, value):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"theme": value}), encoding="utf-8")
    assert load_config(path).theme == "padrao"


def test_missing_theme_key_uses_default(tmp_path: Path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"focus_minutes": 40}), encoding="utf-8")
    assert load_config(path).theme == "padrao"


def test_theme_roundtrip_preserves_value(tmp_path: Path):
    path = tmp_path / "config.json"
    save_config(Config(theme="feminino"), path)
    assert load_config(path).theme == "feminino"
    save_config(Config(theme="escuro"), path)
    assert load_config(path).theme == "escuro"


# ---- formulário de configurações ---------------------------------------------


def test_form_values_include_theme():
    assert form_values(Config(theme="escuro"))["theme"] == "escuro"


def test_build_config_accepts_known_theme():
    raw = {"theme": "feminino"}
    assert build_config(raw, Config()).theme == "feminino"


def test_build_config_rejects_unknown_theme():
    with pytest.raises(SettingsError):
        build_config({"theme": "neon"}, Config())
    with pytest.raises(SettingsError):
        build_config({"theme": None}, Config())


def test_build_config_without_theme_keeps_base():
    assert build_config({}, Config(theme="escuro")).theme == "escuro"


# ---- gráfico -----------------------------------------------------------------


def test_chart_colors_padrao_keeps_original_colors():
    assert chart_colors(PADRAO, dark=False) == _LIGHT
    assert chart_colors(PADRAO, dark=True) == _DARK


@pytest.mark.parametrize("palette", [FEMININO, ESCURO], ids=["feminino", "escuro"])
def test_chart_colors_follow_palette(palette: Palette):
    colors = chart_colors(palette, dark=False)
    assert colors == {"bg": palette.card, "bar": palette.accent, "text": palette.text}
    # O modo do sistema não altera temas com cores próprias.
    assert chart_colors(palette, dark=True) == colors


# ---- smoke de UI (opt-in) ----------------------------------------------------

smoke = pytest.mark.skipif(
    os.environ.get("POMODORO_UI_SMOKE") != "1",
    reason="smoke test de UI: defina POMODORO_UI_SMOKE=1 para executar",
)


@smoke
def test_windows_build_in_every_theme(tmp_path: Path):
    try:
        import customtkinter as ctk

        from pomodoro.ui.controller import PomodoroController
        from pomodoro.ui.main_window import MainWindow
        from pomodoro.ui.settings_dialog import SettingsDialog
        from pomodoro.ui.stats import StatsWindow
    except ImportError as exc:  # pragma: no cover
        pytest.skip(f"customtkinter indisponível: {exc}")

    storage = Storage(tmp_path / "pomodoro.db")
    controller = PomodoroController(Config(theme="feminino"), storage)
    try:
        window = MainWindow(controller, save=lambda c: None, storage=storage)
    except Exception as exc:  # sem display
        storage.close()
        pytest.skip(f"sem display para a janela: {exc}")

    try:
        window.update()
        assert window.cget("fg_color") == FEMININO.bg

        for name in ("escuro", "padrao", "feminino"):
            window._set_theme(name)
            window.update()
            if name == "padrao":
                # Volta às cores do CustomTkinter (tupla do ThemeManager).
                assert window.cget("fg_color") == ctk.ThemeManager.theme["CTk"]["fg_color"]
            else:
                assert window.cget("fg_color") == THEMES[name].bg

        stats = StatsWindow(window, storage, palette=FEMININO)
        stats.update()
        stats.apply_palette(ESCURO)
        stats.apply_palette(PADRAO)
        stats.destroy()

        dialog = SettingsDialog(window, controller.config, on_save=lambda c: None)
        dialog.update()
        for label in THEME_LABELS.values():
            dialog._on_theme_selected(label)
            dialog.update()
        dialog.destroy()
    finally:
        window.destroy()
        storage.close()
