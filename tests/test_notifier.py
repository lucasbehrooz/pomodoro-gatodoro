"""Testes do notifier. winsound e winotify são simulados via sys.modules (Linux)."""

from __future__ import annotations

import logging
import sys
import types

import pytest

from pomodoro import notifier as notifier_mod
from pomodoro.notifier import (
    SYSTEM_ALERT_SOUND,
    NullNotifier,
    WindowsNotifier,
    get_notifier,
)

SND_ALIAS = 0x10000
SND_ASYNC = 0x0001


class FakeWinsound(types.ModuleType):
    SND_ALIAS = SND_ALIAS
    SND_ASYNC = SND_ASYNC

    def __init__(self) -> None:
        super().__init__("winsound")
        self.calls: list[tuple] = []

    def PlaySound(self, sound, flags):  # noqa: N802 - API do winsound
        self.calls.append((sound, flags))


class FakeNotification:
    instances: list["FakeNotification"] = []

    def __init__(self, app_id, title, msg):
        self.app_id = app_id
        self.title = title
        self.msg = msg
        self.shown = False
        FakeNotification.instances.append(self)

    def show(self):
        self.shown = True


@pytest.fixture
def fake_winsound(monkeypatch):
    mod = FakeWinsound()
    monkeypatch.setitem(sys.modules, "winsound", mod)
    return mod


@pytest.fixture
def fake_winotify(monkeypatch):
    FakeNotification.instances = []
    mod = types.ModuleType("winotify")
    mod.Notification = FakeNotification
    monkeypatch.setitem(sys.modules, "winotify", mod)
    return mod


def test_sound_desligado_nao_chama_winsound(fake_winsound):
    n = WindowsNotifier(sound_enabled=False)
    n.alert_sound()
    assert fake_winsound.calls == []


def test_sound_ligado_toca_som_do_sistema_assincrono(fake_winsound):
    n = WindowsNotifier(sound_enabled=True)
    n.alert_sound()
    assert fake_winsound.calls == [(SYSTEM_ALERT_SOUND, SND_ALIAS | SND_ASYNC)]


def test_toast_desligado_nao_chama_winotify(fake_winotify):
    n = WindowsNotifier(toast_enabled=False)
    n.toast("Título", "Mensagem")
    assert FakeNotification.instances == []


def test_toast_chama_winotify_com_title_e_msg(fake_winotify):
    n = WindowsNotifier(app_id="Pomodoro", toast_enabled=True)
    n.toast("Foco concluído", "Hora da pausa")
    assert len(FakeNotification.instances) == 1
    note = FakeNotification.instances[0]
    assert note.app_id == "Pomodoro"
    assert note.title == "Foco concluído"
    assert note.msg == "Hora da pausa"
    assert note.shown is True


def test_import_error_winotify_nao_levanta_e_loga(monkeypatch, caplog):
    # Valor None em sys.modules faz "import" levantar ImportError.
    monkeypatch.setitem(sys.modules, "winotify", None)
    n = WindowsNotifier(toast_enabled=True)
    with caplog.at_level(logging.WARNING, logger=notifier_mod.logger.name):
        n.toast("t", "m")  # não deve levantar
    assert any("toast" in r.getMessage() for r in caplog.records)


def test_import_error_winsound_nao_levanta_e_loga(monkeypatch, caplog):
    monkeypatch.setitem(sys.modules, "winsound", None)
    n = WindowsNotifier(sound_enabled=True)
    with caplog.at_level(logging.WARNING, logger=notifier_mod.logger.name):
        n.alert_sound()  # não deve levantar
    assert any("som" in r.getMessage() for r in caplog.records)


def test_erro_em_notification_nao_levanta(monkeypatch, caplog):
    class Boom:
        def __init__(self, **_kwargs):
            raise RuntimeError("falha do sistema")

    mod = types.ModuleType("winotify")
    mod.Notification = Boom
    monkeypatch.setitem(sys.modules, "winotify", mod)
    n = WindowsNotifier(toast_enabled=True)
    with caplog.at_level(logging.WARNING, logger=notifier_mod.logger.name):
        n.toast("t", "m")  # não deve levantar
    assert caplog.records


def test_get_notifier_fora_do_windows_retorna_null(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    n = get_notifier(sound_enabled=True, toast_enabled=True)
    assert isinstance(n, NullNotifier)


def test_get_notifier_no_windows_retorna_windows_notifier(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    n = get_notifier(sound_enabled=False, toast_enabled=True)
    assert isinstance(n, WindowsNotifier)
    assert n.sound_enabled is False
    assert n.toast_enabled is True


def test_windows_notifier_satisfaz_protocolo():
    n = WindowsNotifier()
    assert callable(getattr(n, "alert_sound", None))
    assert callable(getattr(n, "toast", None))


def test_null_notifier_satisfaz_protocolo():
    n = NullNotifier()
    assert callable(getattr(n, "alert_sound", None))
    assert callable(getattr(n, "toast", None))
    assert n.alert_sound() is None
    assert n.toast("t", "m") is None
