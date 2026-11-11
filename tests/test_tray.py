"""Testes da bandeja. pystray é substituído por um módulo falso; nada depende de display."""

from __future__ import annotations

import sys
import threading
import types

import pytest

from pomodoro import tray as tray_mod
from pomodoro.tray import TrayIcon, make_icon


@pytest.fixture(autouse=True)
def _use_fallback_icon(monkeypatch, tmp_path):
    # Testa o círculo vermelho de reserva; o ícone do gato é coberto em test_icon.py.
    import pomodoro.assets as assets

    monkeypatch.setattr(assets, "ICON_PNG_PATH", tmp_path / "inexistente.png")


class FakeMenu:
    SEPARATOR = object()

    def __init__(self, *items):
        self.items = items


class FakeMenuItem:
    def __init__(self, text, action, default=False):
        self.text = text
        self.action = action
        self.default = default


class FakeIcon:
    instances: list["FakeIcon"] = []
    fail_on_init = False

    def __init__(self, name, icon=None, title=None, menu=None):
        if FakeIcon.fail_on_init:
            raise OSError("sem display")
        self.name = name
        self.icon = icon
        self.title = title
        self.menu = menu
        self.stop_calls = 0
        self._done = threading.Event()
        FakeIcon.instances.append(self)

    def run(self):
        # Bloqueia até stop(), como o pystray real.
        self._done.wait(timeout=5)

    def stop(self):
        self.stop_calls += 1
        self._done.set()


@pytest.fixture
def fake_pystray(monkeypatch):
    FakeIcon.instances = []
    FakeIcon.fail_on_init = False
    module = types.ModuleType("pystray")
    module.Icon = FakeIcon
    module.Menu = FakeMenu
    module.MenuItem = FakeMenuItem
    monkeypatch.setitem(sys.modules, "pystray", module)
    yield module
    # Garante que nenhuma thread fique presa entre testes.
    for icon in FakeIcon.instances:
        icon.stop()


def _make_tray(title="Pomodoro"):
    calls = {"toggle": [], "show": [], "quit": []}
    tray = TrayIcon(
        on_toggle=lambda: calls["toggle"].append(threading.get_ident()),
        on_show=lambda: calls["show"].append(threading.get_ident()),
        on_quit=lambda: calls["quit"].append(threading.get_ident()),
        title=title,
    )
    return tray, calls


def test_menu_has_expected_items(fake_pystray):
    tray, _ = _make_tray()
    tray.start()
    menu = FakeIcon.instances[-1].menu
    items = menu.items
    assert [getattr(i, "text", i) for i in items] == [
        "Iniciar/Pausar",
        "Abrir",
        FakeMenu.SEPARATOR,
        "Sair",
    ]
    assert items[1].default is True
    tray.stop()


def test_menu_actions_only_enqueue_events(fake_pystray):
    tray, calls = _make_tray()
    tray.start()
    items = FakeIcon.instances[-1].menu.items
    icon = FakeIcon.instances[-1]

    # Simula a thread do pystray disparando os itens.
    worker = threading.Thread(
        target=lambda: [items[0].action(icon, items[0]), items[1].action(icon, items[1]),
                        items[3].action(icon, items[3])]
    )
    worker.start()
    worker.join()

    # Nenhum callback rodou ainda: só a fila foi preenchida.
    assert calls == {"toggle": [], "show": [], "quit": []}
    assert list(tray.events.queue) == ["toggle", "show", "quit"]
    tray.stop()


def test_poll_runs_callbacks_in_calling_thread(fake_pystray):
    tray, calls = _make_tray()
    tray.events.put("toggle")
    tray.events.put("show")
    tray.events.put("quit")

    handled = tray.poll()

    assert handled == 3
    me = threading.get_ident()
    assert calls["toggle"] == [me]
    assert calls["show"] == [me]
    assert calls["quit"] == [me]


def test_poll_on_empty_queue_is_noop(fake_pystray):
    tray, calls = _make_tray()
    assert tray.poll() == 0
    assert calls == {"toggle": [], "show": [], "quit": []}


def test_poll_continues_after_callback_error(fake_pystray):
    calls = []

    def boom():
        raise RuntimeError("falha")

    tray = TrayIcon(on_toggle=boom, on_show=lambda: calls.append("show"), on_quit=lambda: None)
    tray.events.put("toggle")
    tray.events.put("show")

    assert tray.poll() == 2
    assert calls == ["show"]


def test_set_status_before_start_is_applied_on_start(fake_pystray):
    tray, _ = _make_tray()
    tray.set_status("Foco 24:10", True)
    tray.start()

    icon = FakeIcon.instances[-1]
    assert icon.title == "Foco 24:10"
    # Estado "rodando" tem ponto branco no centro.
    assert icon.icon.getpixel((32, 32)) == (255, 255, 255, 255)
    tray.stop()


def test_set_status_after_start_updates_title_and_icon(fake_pystray):
    tray, _ = _make_tray()
    tray.start()
    icon = FakeIcon.instances[-1]

    tray.set_status("Pausado", False)

    assert icon.title == "Pausado"
    assert icon.icon.getpixel((32, 32)) != (255, 255, 255, 255)
    tray.stop()


def test_stop_is_idempotent(fake_pystray):
    tray, _ = _make_tray()
    tray.start()
    icon = FakeIcon.instances[-1]

    tray.stop()
    tray.stop()

    assert icon.stop_calls == 1


def test_stop_without_start_is_safe(fake_pystray):
    tray, _ = _make_tray()
    tray.stop()
    tray.stop()


def test_start_twice_creates_single_icon(fake_pystray):
    tray, _ = _make_tray()
    tray.start()
    tray.start()
    assert len(FakeIcon.instances) == 1
    tray.stop()


def test_start_failure_does_not_raise_and_marks_unavailable(fake_pystray):
    FakeIcon.fail_on_init = True
    tray, _ = _make_tray()

    tray.start()  # não deve levantar

    assert tray.is_available is False
    tray.stop()  # continua seguro


def test_start_without_pystray_is_unavailable(monkeypatch):
    # sys.modules[name] = None faz o import falhar.
    monkeypatch.setitem(sys.modules, "pystray", None)
    tray, _ = _make_tray()
    tray.start()
    assert tray.is_available is False


def test_set_status_is_safe_without_icon(fake_pystray):
    tray, _ = _make_tray()
    tray.set_status("qualquer", False)  # não deve levantar
    assert tray.is_available is False


def test_make_icon_returns_64x64_image():
    image = make_icon(running=False)
    assert image.size == (tray_mod.ICON_SIZE, tray_mod.ICON_SIZE) == (64, 64)
    assert image.mode == "RGBA"
    # Centro do círculo vermelho, canto transparente.
    assert image.getpixel((8, 32))[:3] == (200, 40, 40)
    assert image.getpixel((0, 0))[3] == 0


def test_make_icon_running_differs_from_idle():
    assert make_icon(True).tobytes() != make_icon(False).tobytes()
