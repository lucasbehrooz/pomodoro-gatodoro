"""Entry point do Pomodoro."""

from __future__ import annotations

import logging

from pomodoro.config import load_config
from pomodoro.notifier import get_notifier
from pomodoro.storage import Storage
from pomodoro.tray import TrayIcon
from pomodoro.ui.controller import NoiseControl, PomodoroController
from pomodoro.ui.main_window import MainWindow

logger = logging.getLogger(__name__)

TRAY_POLL_MS = 100


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
        # Callbacks da bandeja rodam na thread do pystray: sempre via window.post().
        tray = TrayIcon(
            on_toggle=lambda: window.post(controller.toggle),
            on_show=lambda: window.post(window.show_window),
            on_quit=lambda: window.post(window.quit_app),
        )
        tray.start()
        # Sem bandeja disponível, "fechar para a bandeja" esconderia a janela sem volta.
        window = MainWindow(controller, can_hide_to_tray=tray.is_available, storage=storage)
        _start_tray_loop(window, controller, tray)
        try:
            window.mainloop()
        finally:
            tray.stop()
    finally:
        storage.close()


def _start_tray_loop(window: MainWindow, controller: PomodoroController, tray: TrayIcon) -> None:
    """Consome a fila da bandeja na thread do Tk e mantém tooltip/ícone atualizados."""

    last: tuple[str, bool] | None = None

    def loop() -> None:
        nonlocal last
        tray.poll()
        state = (controller.phase_label, controller.is_running)
        if state != last:  # set_status troca a imagem do ícone: só quando muda
            tray.set_status(*state)
            last = state
        window.after(TRAY_POLL_MS, loop)

    window.after(TRAY_POLL_MS, loop)


if __name__ == "__main__":
    main()
