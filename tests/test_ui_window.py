"""Smoke test da janela. Abre uma janela Tk real, então só roda com opt-in:

    POMODORO_UI_SMOKE=1 pytest tests/test_ui_window.py

Sem o opt-in, ou sem display disponível, o teste é pulado.
"""

import os
from pathlib import Path

import pytest

from pomodoro.config import Config
from pomodoro.storage import Storage
from pomodoro.ui.controller import PomodoroController

pytestmark = pytest.mark.skipif(
    os.environ.get("POMODORO_UI_SMOKE") != "1",
    reason="smoke test de UI: defina POMODORO_UI_SMOKE=1 para executar",
)


def test_window_smoke(tmp_path: Path):
    try:
        from pomodoro.ui.main_window import MainWindow
    except ImportError as exc:  # pragma: no cover
        pytest.skip(f"customtkinter indisponível: {exc}")

    storage = Storage(tmp_path / "pomodoro.db")
    controller = PomodoroController(Config(), storage)
    try:
        window = MainWindow(controller, save=lambda c: None)
    except Exception as exc:  # sem display
        storage.close()
        pytest.skip(f"sem display para a janela: {exc}")

    try:
        window.update()
        window.show_window()
        window.hide_to_tray()  # withdraw() por padrão
        window.quit_app()
    finally:
        storage.close()


def test_autostart_failure_shows_warning_without_breaking(tmp_path: Path):
    try:
        from pomodoro.ui.main_window import MainWindow
    except ImportError as exc:  # pragma: no cover
        pytest.skip(f"customtkinter indisponível: {exc}")

    storage = Storage(tmp_path / "pomodoro.db")
    controller = PomodoroController(Config(), storage)
    saved: list[Config] = []

    def failing_autostart(enabled: bool) -> None:
        raise PermissionError("registro bloqueado")

    try:
        window = MainWindow(
            controller,
            save=saved.append,
            autostart=failing_autostart,
        )
    except Exception as exc:  # sem display
        storage.close()
        pytest.skip(f"sem display para a janela: {exc}")

    try:
        window._save_settings(Config(start_with_windows=True))
        text = window._status_label.cget("text")
        assert saved and saved[0].start_with_windows is True
        assert "Iniciar com o Windows" in text
        assert "registro bloqueado" in text
    finally:
        window.quit_app()
        storage.close()
