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


def test_update_banner_download_and_skip(tmp_path: Path):
    try:
        from pomodoro.ui.main_window import MainWindow
        from pomodoro.updater import UpdateInfo
    except ImportError as exc:  # pragma: no cover
        pytest.skip(f"customtkinter indisponível: {exc}")

    storage = Storage(tmp_path / "pomodoro.db")
    controller = PomodoroController(Config(), storage)
    saved: list[Config] = []
    opened: list[str] = []
    try:
        window = MainWindow(controller, save=saved.append, open_url=opened.append)
    except Exception as exc:  # sem display
        storage.close()
        pytest.skip(f"sem display para a janela: {exc}")

    try:
        info = UpdateInfo("9.9.9", "https://example.test/r")
        window.show_update(info)
        assert window._update_banner.winfo_manager() == "pack"
        assert "9.9.9" in window._update_label.cget("text")

        window._on_update_download()
        assert opened == ["https://example.test/r"]
        assert not window._update_banner.winfo_manager()

        window.show_update(info)
        window._on_update_skip()
        assert saved and saved[-1].skipped_version == "9.9.9"
        assert controller.config.skipped_version == "9.9.9"
        assert not window._update_banner.winfo_manager()
    finally:
        window.quit_app()
        storage.close()


def test_open_stats_refresh_after_skip(tmp_path: Path):
    try:
        from pomodoro.ui.main_window import MainWindow
    except ImportError as exc:  # pragma: no cover
        pytest.skip(f"customtkinter indisponível: {exc}")

    storage = Storage(tmp_path / "pomodoro.db")
    controller = PomodoroController(Config(), storage)
    try:
        window = MainWindow(controller, save=lambda c: None, storage=storage)
    except Exception as exc:  # sem display
        storage.close()
        pytest.skip(f"sem display para a janela: {exc}")

    try:
        window._open_stats()
        refreshed: list[bool] = []
        original = window._stats_window.refresh
        window._stats_window.refresh = lambda: (refreshed.append(True), original())
        window._on_skip()
        window._on_reset()
        assert refreshed == [True, True]
    finally:
        window.quit_app()
        storage.close()
