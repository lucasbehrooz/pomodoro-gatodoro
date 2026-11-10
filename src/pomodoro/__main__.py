"""Entry point do Pomodoro."""

from __future__ import annotations

import importlib.util
import logging

from pomodoro.config import load_config
from pomodoro.notifier import get_notifier
from pomodoro.storage import Storage
from pomodoro.ui.controller import NoiseControl, PomodoroController
from pomodoro.ui.main_window import MainWindow

logger = logging.getLogger(__name__)


def _make_noise_player() -> NoiseControl | None:
    """Player de ruído, se o módulo existir. Sem ele, o app roda sem ruído."""
    try:
        from pomodoro.noise import BrownNoisePlayer  # type: ignore[attr-defined]
    except ImportError:
        logger.info("Player de ruído indisponível; ruído marrom desativado")
        return None
    try:
        return BrownNoisePlayer()  # type: ignore[no-any-return]
    except Exception:
        logger.exception("Falha ao criar o player de ruído")
        return None


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    config = load_config()
    storage = Storage()
    try:
        controller = PomodoroController(
            config,
            storage,
            notifier=get_notifier(config.sound_enabled, config.toast_enabled),
            noise_player=_make_noise_player(),
            notifier_factory=lambda c: get_notifier(c.sound_enabled, c.toast_enabled),
        )
        # Sem módulo de bandeja, "fechar para a bandeja" esconderia a janela sem volta.
        can_hide = importlib.util.find_spec("pomodoro.tray") is not None
        window = MainWindow(controller, can_hide_to_tray=can_hide)
        window.mainloop()
    finally:
        storage.close()


if __name__ == "__main__":
    main()
