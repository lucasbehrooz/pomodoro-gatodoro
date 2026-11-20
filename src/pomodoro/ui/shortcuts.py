"""Atalhos de teclado da janela principal (lógica pura, sem Tk).

A janela recebe o evento de tecla e pergunta a ``shortcut_action`` qual ação
executar. Assim a regra (qual tecla, quando ignorar) é testada sem display.
"""

from __future__ import annotations

import sys
from enum import Enum


class ShortcutAction(Enum):
    TOGGLE = "toggle"  # Iniciar/Pausar
    RESET = "reset"  # Reiniciar
    SKIP = "skip"  # Pular


# keysym do Tk -> ação. Maiúsculas cobrem Shift e Caps Lock.
KEY_ACTIONS: dict[str, ShortcutAction] = {
    "space": ShortcutAction.TOGGLE,
    "r": ShortcutAction.RESET,
    "R": ShortcutAction.RESET,
    "s": ShortcutAction.SKIP,
    "S": ShortcutAction.SKIP,
}

# Classes Tk de widgets em que se digita texto. CTkEntry/CTkTextbox usam
# Entry/Text por dentro; as demais cobrem widgets ttk e Tk puros.
TEXT_INPUT_CLASSES = frozenset({"Entry", "TEntry", "Text", "Spinbox", "TSpinbox", "TCombobox"})

# Bits de ``event.state``. Ctrl é igual em todas as plataformas. Alt é 0x20000
# no Windows; no X11 é Mod1 (0x8), que no Windows indica Num Lock e não pode
# bloquear o atalho.
STATE_CONTROL = 0x4
STATE_ALT = 0x20000 if sys.platform == "win32" else 0x8

HINT_TEXT = "Espaço: iniciar/pausar · R: reiniciar · S: pular"


def shortcut_action(
    keysym: str,
    *,
    widget_class: str = "",
    in_main_window: bool = True,
    state: int = 0,
    alt_mask: int = STATE_ALT,
) -> ShortcutAction | None:
    """Ação do atalho para a tecla, ou None se o evento deve ser ignorado.

    Ignora teclas sem atalho, eventos vindos de outras janelas (Configurações,
    Estatísticas), de campos de texto e combinações com Ctrl ou Alt.
    """
    if not in_main_window:
        return None
    if widget_class in TEXT_INPUT_CLASSES:
        return None
    if state & (STATE_CONTROL | alt_mask):
        return None
    return KEY_ACTIONS.get(keysym)


# No X11 a repetição automática gera pares KeyRelease/KeyPress com o mesmo
# horário (ou quase). Uma soltura seguida de um aperto em até este intervalo
# é tratada como repetição, não como um novo aperto.
REPEAT_GAP_MS = 20


class KeyRepeatFilter:
    """Aceita só o primeiro aperto de cada tecla de atalho até ela ser solta.

    Segurar Espaço ou S não pode alternar ou pular várias vezes. No Windows a
    repetição automática manda só KeyPress repetidos (a tecla continua
    "segurada"); no X11 manda KeyRelease + KeyPress no mesmo instante.
    ``time`` é o ``event.time`` do Tk, em milissegundos.
    """

    def __init__(self, repeat_gap_ms: int = REPEAT_GAP_MS) -> None:
        self._repeat_gap_ms = repeat_gap_ms
        self._held: set[ShortcutAction] = set()
        self._released_at: dict[ShortcutAction, int] = {}

    def press(self, action: ShortcutAction, time: int) -> bool:
        """True se o aperto deve executar a ação; False se é repetição."""
        if action in self._held:
            return False
        self._held.add(action)
        released_at = self._released_at.pop(action, None)
        if released_at is not None and 0 <= time - released_at <= self._repeat_gap_ms:
            return False
        return True

    def release(self, keysym: str, time: int) -> None:
        action = KEY_ACTIONS.get(keysym)
        if action is None or action not in self._held:
            return
        self._held.discard(action)
        self._released_at[action] = time

    def reset(self) -> None:
        """Esquece as teclas seguradas (ex.: a janela perdeu o foco antes da soltura)."""
        self._held.clear()
        self._released_at.clear()
