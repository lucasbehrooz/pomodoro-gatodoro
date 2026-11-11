"""Ícone do app nas janelas Tk (barra de título e barra de tarefas)."""

from __future__ import annotations

import logging
from typing import Any

from pomodoro.assets import ICON_ICO_PATH

logger = logging.getLogger(__name__)

# CTkToplevel reaplica o ícone padrão do CustomTkinter logo após criar a janela,
# então o ícone também é reaplicado depois de um pequeno atraso.
_REAPPLY_DELAY_MS = 250


def apply_window_icon(window: Any) -> None:
    """Aplica o .ico do gato à janela agora e de novo logo após a criação.

    Falha não é fatal: o app segue com o ícone padrão.
    """
    _set_icon(window)
    try:
        window.after(_REAPPLY_DELAY_MS, lambda: _set_icon(window))
    except Exception:
        logger.debug("Não foi possível agendar a reaplicação do ícone", exc_info=True)


def _set_icon(window: Any) -> None:
    try:
        if ICON_ICO_PATH.exists():
            window.iconbitmap(str(ICON_ICO_PATH))
    except Exception:
        logger.warning("Não foi possível aplicar o ícone da janela", exc_info=True)
