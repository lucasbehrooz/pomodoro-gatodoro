"""Temas visuais: paletas tipadas e funções que aplicam cores aos widgets CustomTkinter.

Convenção: em uma Palette, campo ``None`` significa "usar o padrão do CustomTkinter"
(lido do ``ThemeManager``). Só o tema "padrao" usa ``None``, e assim mantém a
aparência original, inclusive o modo claro/escuro do sistema. Os demais temas
definem todas as cores em hexadecimal (#RRGGBB).

Este módulo não importa customtkinter no topo: a importação é preguiçosa, para
que ``config.py`` possa validar o nome do tema sem carregar a interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    import customtkinter as ctk

DEFAULT_THEME = "padrao"


@dataclass(frozen=True)
class Palette:
    name: str
    bg: str | None  # fundo da janela
    card: str | None  # fundo de cards e frames
    text: str | None  # texto principal
    muted: str | None  # texto secundário
    accent: str | None  # botões, barras, seleção
    accent_hover: str | None  # botões em hover
    button_text: str | None  # texto sobre o accent
    entry_bg: str | None  # fundo de campos de entrada
    warning: str  # aviso (ex.: configurações pendentes)
    error: str  # erro de validação


PADRAO = Palette(
    name="padrao",
    bg=None,
    card=None,
    text=None,
    muted=None,
    accent=None,
    accent_hover=None,
    button_text=None,
    entry_bg=None,
    warning="#f0ad4e",
    error="#d9534f",
)

FEMININO = Palette(
    name="feminino",
    bg="#FDF0F5",
    card="#F7E6F0",
    text="#4A1F3D",
    muted="#8A5A78",
    accent="#E0609A",
    accent_hover="#C94C86",
    button_text="#000000",
    entry_bg="#FFFFFF",
    warning="#9A5B00",
    error="#A4262C",
)

ESCURO = Palette(
    name="escuro",
    bg="#1F2328",
    card="#2B2F36",
    text="#E6E9EF",
    muted="#9AA3B2",
    accent="#7CB8F2",
    accent_hover="#5FA3E6",
    button_text="#0B1A2A",
    entry_bg="#14171C",
    warning="#F0AD4E",
    error="#FF7B72",
)

THEMES: dict[str, Palette] = {
    "padrao": PADRAO,
    "feminino": FEMININO,
    "escuro": ESCURO,
}

THEME_LABELS: dict[str, str] = {
    "padrao": "Padrão",
    "feminino": "Feminino",
    "escuro": "Escuro",
}


def is_valid_theme(name: object) -> bool:
    """True se ``name`` é uma chave conhecida de THEMES. Não-strings são inválidas."""
    return isinstance(name, str) and name in THEMES


def get_palette(name: object) -> Palette:
    """Paleta do tema ``name``. Nomes desconhecidos (ou não-string) retornam a padrão."""
    if not is_valid_theme(name):
        return PADRAO
    return THEMES[name]  # type: ignore[index]


def theme_label(key: str) -> str:
    """Rótulo em português exibido no seletor. Chave desconhecida vira o rótulo padrão."""
    return THEME_LABELS.get(key, THEME_LABELS[DEFAULT_THEME])


def theme_key_from_label(label: str) -> str | None:
    """Chave do tema para um rótulo do seletor; None se o rótulo for desconhecido."""
    for key, text in THEME_LABELS.items():
        if text == label:
            return key
    return None


# ---- aplicação aos widgets -------------------------------------------------


def _ctk_default(widget: str, prop: str) -> Any:
    import customtkinter as ctk

    return ctk.ThemeManager.theme[widget][prop]


def _c(value: str | None, widget: str, prop: str) -> Any:
    """Cor da paleta, ou o padrão do CustomTkinter para ``widget.prop`` se ``value`` é None."""
    return value if value is not None else _ctk_default(widget, prop)


def apply_window(win: Any, p: Palette, widget: str = "CTk") -> None:
    """Fundo de janela. ``widget`` é "CTk" (janela principal) ou "CTkToplevel" (diálogos)."""
    win.configure(fg_color=_c(p.bg, widget, "fg_color"))


def apply_card(frame: ctk.CTkFrame, p: Palette) -> None:
    frame.configure(fg_color=_c(p.card, "CTkFrame", "fg_color"))


def apply_text(label: ctk.CTkLabel, p: Palette, *, muted: bool = False) -> None:
    label.configure(text_color=_c(p.muted if muted else p.text, "CTkLabel", "text_color"))


def apply_accent_button(btn: ctk.CTkButton, p: Palette) -> None:
    btn.configure(
        fg_color=_c(p.accent, "CTkButton", "fg_color"),
        hover_color=_c(p.accent_hover, "CTkButton", "hover_color"),
        text_color=_c(p.button_text, "CTkButton", "text_color"),
    )


def apply_entry(entry: ctk.CTkEntry, p: Palette) -> None:
    entry.configure(
        fg_color=_c(p.entry_bg, "CTkEntry", "fg_color"),
        text_color=_c(p.text, "CTkEntry", "text_color"),
    )


def apply_checkbox(box: ctk.CTkCheckBox, p: Palette) -> None:
    box.configure(
        fg_color=_c(p.accent, "CTkCheckBox", "fg_color"),
        hover_color=_c(p.accent_hover, "CTkCheckBox", "hover_color"),
        checkmark_color=_c(p.button_text, "CTkCheckBox", "checkmark_color"),
        text_color=_c(p.text, "CTkCheckBox", "text_color"),
    )


def apply_slider(slider: ctk.CTkSlider, p: Palette) -> None:
    slider.configure(
        button_color=_c(p.accent, "CTkSlider", "button_color"),
        button_hover_color=_c(p.accent_hover, "CTkSlider", "button_hover_color"),
        progress_color=_c(p.accent, "CTkSlider", "progress_color"),
    )


def apply_option_menu(menu: ctk.CTkOptionMenu, p: Palette) -> None:
    menu.configure(
        fg_color=_c(p.accent, "CTkOptionMenu", "fg_color"),
        button_color=_c(p.accent_hover, "CTkOptionMenu", "button_color"),
        button_hover_color=_c(p.accent_hover, "CTkOptionMenu", "button_hover_color"),
        text_color=_c(p.button_text, "CTkOptionMenu", "text_color"),
        dropdown_fg_color=_c(p.card, "DropdownMenu", "fg_color"),
        dropdown_hover_color=_c(p.entry_bg, "DropdownMenu", "hover_color"),
        dropdown_text_color=_c(p.text, "DropdownMenu", "text_color"),
    )


def refresh_transparent_bg(widget: Any) -> None:
    """Recalcula a cor de fundo herdada dos widgets CTk filhos.

    Widgets CTk copiam a cor do master na criação. Depois que a cor da janela
    muda, cantos e áreas transparentes continuariam com a cor antiga. Percorre
    a árvore de cima para baixo, para que cada filho leia a cor já atualizada do pai.
    """
    import customtkinter as ctk

    for child in widget.winfo_children():
        if isinstance(child, ctk.CTkBaseClass):
            child.configure(bg_color="transparent")
        refresh_transparent_bg(child)
