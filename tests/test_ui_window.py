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
from pomodoro.ui.shortcuts import HINT_TEXT

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


def test_update_banner_follows_manager_and_skip(tmp_path: Path):
    try:
        from pomodoro.ui.main_window import MainWindow
        from pomodoro.updater import UpdateInfo, UpdateManager, UpdateState
    except ImportError as exc:  # pragma: no cover
        pytest.skip(f"customtkinter indisponível: {exc}")

    storage = Storage(tmp_path / "pomodoro.db")
    controller = PomodoroController(Config(), storage)
    saved: list[Config] = []
    info = UpdateInfo("9.9.9", "https://example.test/r", "https://example.test/setup.exe")
    updates = UpdateManager(
        post=lambda fn: fn(),
        quit_app=lambda: None,
        check=lambda current: info,
        start_thread=lambda fn: fn(),
    )
    try:
        window = MainWindow(controller, save=saved.append, updates=updates)
    except Exception as exc:  # sem display
        storage.close()
        pytest.skip(f"sem display para a janela: {exc}")

    try:
        assert not window._update_banner.winfo_manager()
        updates.check()
        assert updates.state is UpdateState.AVAILABLE
        assert window._update_banner.winfo_manager() == "pack"
        assert "9.9.9" in window._update_label.cget("text")

        # "Atualizar" abre as Configurações, já com o botão de atualizar.
        window._update_download_btn.invoke()
        dialog = window._settings_dialog
        assert dialog is not None and dialog.winfo_exists()
        assert dialog._install_btn.winfo_manager() == "pack"
        assert "9.9.9" in dialog._install_btn.cget("text")
        dialog.destroy()

        window._on_update_skip()
        assert saved and saved[-1].skipped_version == "9.9.9"
        assert not window._update_banner.winfo_manager()
        updates.check()  # versão ignorada: o aviso não volta
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


def _make_window(tmp_path: Path):
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
    return window, controller, storage


_clock = iter(range(10_000, 10_000_000, 500))  # horário dos eventos, em ms


def _press(widget, key: str) -> None:
    """Aperta e solta a tecla, como um toque normal."""
    t = next(_clock)
    widget.event_generate(f"<KeyPress-{key}>", time=t)
    widget.event_generate(f"<KeyRelease-{key}>", time=t + 80)
    widget.update()


def test_keyboard_shortcuts_call_button_handlers(tmp_path: Path):
    window, controller, storage = _make_window(tmp_path)
    calls: list[str] = []
    try:
        for name in ("_on_toggle", "_on_reset", "_on_skip"):
            original = getattr(window, name)

            def wrapper(original=original, name=name):
                calls.append(name)
                original()

            setattr(window, name, wrapper)
        window.update()
        target = window._time_label  # widget comum da janela principal

        _press(target, "space")
        assert controller.is_running
        assert window._toggle_btn.cget("text") == "Pausar"
        _press(target, "space")
        assert not controller.is_running
        _press(target, "s")
        _press(target, "S")
        _press(target, "r")
        _press(target, "R")
        _press(target, "x")  # sem atalho
        assert calls == [
            "_on_toggle",
            "_on_toggle",
            "_on_skip",
            "_on_skip",
            "_on_reset",
            "_on_reset",
        ]
        assert window._hint_label.cget("text") == HINT_TEXT
    finally:
        window.quit_app()
        storage.close()


def test_keyboard_shortcuts_ignored_in_text_fields_and_child_windows(tmp_path: Path):
    import customtkinter as ctk

    window, controller, storage = _make_window(tmp_path)
    try:
        entry = ctk.CTkEntry(window)
        entry.pack()
        child = ctk.CTkToplevel(window)
        child_label = ctk.CTkLabel(child, text="filha")
        child_label.pack()
        child_entry = ctk.CTkEntry(child)
        child_entry.pack()
        window.update()

        for widget in (entry._entry, child_label, child_entry._entry, child):
            _press(widget, "space")
            _press(widget, "s")
            _press(widget, "r")
        assert not controller.is_running
        assert controller.completed_focus_count == 0
        assert window._toggle_btn.cget("text") == "Iniciar"

        # Digitar no campo continua funcionando.
        entry._entry.focus_force()
        entry._entry.insert("end", "rs ")
        assert entry.get() == "rs "
        child.destroy()
    finally:
        window.quit_app()
        storage.close()


@pytest.mark.parametrize("theme", ["padrao", "feminino", "escuro"])
def test_hint_follows_theme(tmp_path: Path, theme: str):
    from pomodoro.ui.theme import get_palette

    window, controller, storage = _make_window(tmp_path)
    try:
        window._set_theme(theme)
        window.update()
        palette = get_palette(theme)
        expected = palette.muted
        if expected is None:  # tema padrao: cor padrão do CustomTkinter
            import customtkinter as ctk

            expected = ctk.ThemeManager.theme["CTkLabel"]["text_color"]
        assert window._hint_label.cget("text_color") == expected
    finally:
        window.quit_app()
        storage.close()


def test_held_key_does_not_repeat(tmp_path: Path):
    window, controller, storage = _make_window(tmp_path)
    calls: list[str] = []
    try:
        for name in ("_on_toggle", "_on_skip"):
            original = getattr(window, name)

            def wrapper(original=original, name=name):
                calls.append(name)
                original()

            setattr(window, name, wrapper)
        window.update()
        target = window._time_label

        # Windows: segurar S gera só KeyPress repetidos.
        start = next(_clock)
        for i in range(10):
            target.event_generate("<KeyPress-s>", time=start + 33 * i)
        target.event_generate("<KeyRelease-s>", time=start + 400)
        target.update()
        assert calls == ["_on_skip"]
        _press(target, "s")  # novo toque pula de novo
        assert calls == ["_on_skip", "_on_skip"]

        # X11: segurar Espaço gera pares KeyRelease/KeyPress no mesmo instante.
        t = next(_clock)
        target.event_generate("<KeyPress-space>", time=t)
        for i in range(1, 10):
            target.event_generate("<KeyRelease-space>", time=t + 33 * i)
            target.event_generate("<KeyPress-space>", time=t + 33 * i)
        target.event_generate("<KeyRelease-space>", time=t + 400)
        target.update()
        assert calls == ["_on_skip", "_on_skip", "_on_toggle"]
        assert controller.is_running
    finally:
        window.quit_app()
        storage.close()


# ---- meta diária e altura da janela ------------------------------------------


def test_daily_goal_label_and_stats_goal_line(tmp_path: Path):
    try:
        from pomodoro.ui.main_window import MainWindow
    except ImportError as exc:  # pragma: no cover
        pytest.skip(f"customtkinter indisponível: {exc}")

    from dataclasses import replace

    storage = Storage(tmp_path / "pomodoro.db")
    controller = PomodoroController(Config(daily_goal=8), storage)
    try:
        window = MainWindow(controller, save=lambda c: None, storage=storage)
    except Exception as exc:  # sem display
        storage.close()
        pytest.skip(f"sem display para a janela: {exc}")

    try:
        window.update()
        assert window._goal_label.cget("text") == "Hoje: 0/8"
        window._open_stats()
        window.update()
        stats = window._stats_window
        assert stats._canvas.find_withtag("goal_line")
        assert stats._goal_legend.cget("text").endswith("Meta diária: 8")

        # Salvar a meta nova redesenha as Estatísticas abertas na hora.
        window._save_settings(replace(controller.config, daily_goal=5))
        window.update()
        assert window._goal_label.cget("text") == "Hoje: 0/5"
        assert stats._goal_legend.cget("text").endswith("Meta diária: 5")

        window._save_settings(replace(controller.config, daily_goal=0))
        window.update()
        assert window._goal_label.cget("text") == ""
        assert not stats._canvas.find_withtag("goal_line")
        assert not stats._goal_legend.winfo_manager()
    finally:
        window.quit_app()
        storage.close()


def _content_height(window) -> int:
    """Altura pedida pelos widgets empacotados na janela (todos empilhados na vertical)."""
    total = 0
    for child in window.pack_slaves():
        pady = child.pack_info()["pady"]
        pad = sum(int(p) for p in pady) if isinstance(pady, tuple) else 2 * int(pady)
        total += child.winfo_reqheight() + pad
    return total


def test_window_content_fits_height_with_and_without_update_banner(tmp_path: Path):
    """Protege a soma das linhas (dica dos atalhos, "Hoje: x/y"...) contra WINDOW_HEIGHT."""
    try:
        from pomodoro.ui.main_window import UPDATE_BANNER_HEIGHT, WINDOW_HEIGHT, MainWindow
        from pomodoro.updater import UpdateInfo, UpdateManager
    except ImportError as exc:  # pragma: no cover
        pytest.skip(f"customtkinter indisponível: {exc}")

    storage = Storage(tmp_path / "pomodoro.db")
    controller = PomodoroController(Config(daily_goal=8), storage)
    info = UpdateInfo("9.9.9", "https://example.test/r", "https://example.test/setup.exe")
    updates = UpdateManager(
        post=lambda fn: fn(),
        quit_app=lambda: None,
        check=lambda current: info,
        start_thread=lambda fn: fn(),
    )
    try:
        window = MainWindow(controller, save=lambda c: None, updates=updates)
    except Exception as exc:  # sem display
        storage.close()
        pytest.skip(f"sem display para a janela: {exc}")

    try:
        controller.apply_config(Config(daily_goal=8))
        window._pending_label.configure(text="Novas durações serão aplicadas ao reiniciar.")
        window._status_label.configure(text="Configurações salvas e aplicadas.")
        window.update()
        assert window._goal_label.cget("text") == "Hoje: 0/8"
        assert window._hint_label.cget("text") == HINT_TEXT
        limit = window._apply_window_scaling(WINDOW_HEIGHT)
        assert _content_height(window) <= limit

        updates.check()
        window.update()
        assert window._update_banner.winfo_manager() == "pack"
        limit = window._apply_window_scaling(WINDOW_HEIGHT + UPDATE_BANNER_HEIGHT)
        assert _content_height(window) <= limit
    finally:
        window.quit_app()
        storage.close()
