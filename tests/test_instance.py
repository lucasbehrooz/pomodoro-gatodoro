import sys
from pathlib import Path

import pytest

from pomodoro.instance import QUIT_EVENT_NAME, RUNNING_MUTEX_NAME, InstanceSignals

ISS = Path(__file__).resolve().parents[1] / "packaging" / "pomodoro.iss"


def test_names_match_installer_script():
    """O instalador fecha o app por esses nomes: os dois lados precisam bater."""
    text = ISS.read_text(encoding="utf-8")
    assert f"RunningMutexName = '{RUNNING_MUTEX_NAME}';" in text
    assert f"QuitEventName = '{QUIT_EVENT_NAME}';" in text


def test_installer_closes_app_before_install():
    text = ISS.read_text(encoding="utf-8")
    assert "function PrepareToInstall" in text
    assert "taskkill.exe" in text and "/F /IM {#MyAppExeName}" in text


@pytest.mark.skipif(sys.platform == "win32", reason="fora do Windows é no-op")
def test_noop_outside_windows():
    called = []
    signals = InstanceSignals()
    assert signals.already_running is False  # o app abre normalmente
    assert signals.notify_existing() is False
    signals.listen(lambda: called.append("quit"), lambda: called.append("show"))
    signals.close()
    signals.close()  # idempotente
    assert called == []


# ---- instância única, com kernel32 falso -----------------------------------

from pomodoro import instance as instance_mod  # noqa: E402
from pomodoro.instance import (  # noqa: E402
    ERROR_ALREADY_EXISTS,
    SHOW_EVENT_NAME,
)

WAIT_FAILED = 0xFFFFFFFF


class FakeKernel32:
    """Imita o pedaço do kernel32 que o app usa: objetos nomeados compartilhados
    entre "processos" (instâncias de InstanceSignals) e um roteiro de esperas."""

    def __init__(self):
        self.last_error = 0
        self.names: dict[str, int] = {}
        self.handles: dict[int, str] = {}
        self.signaled: dict[str, bool] = {}
        self.manual_reset: dict[str, bool] = {}
        self.wait_script: dict[str, list[int]] = {}
        self.closed: list[int] = []
        self.calls: list[tuple] = []
        self._next = 100
        self.fail_mutex = False

    def _open(self, name):
        if name in self.names:
            self.last_error = ERROR_ALREADY_EXISTS
        else:
            self.last_error = 0
            self.names[name] = 1
        self._next += 1
        self.handles[self._next] = name
        return self._next

    def CreateMutexW(self, attrs, initial_owner, name):
        self.calls.append(("CreateMutexW", name))
        if self.fail_mutex:
            self.last_error = 5
            return 0
        return self._open(name)

    def CreateEventW(self, attrs, manual_reset, initial_state, name):
        self.calls.append(("CreateEventW", name, bool(manual_reset)))
        is_new = name not in self.names
        handle = self._open(name)
        if is_new:
            self.manual_reset[name] = bool(manual_reset)
            self.signaled[name] = bool(initial_state)
        return handle

    def SetEvent(self, handle):
        name = self.handles[handle]
        self.calls.append(("SetEvent", name))
        self.signaled[name] = True
        return 1

    def ResetEvent(self, handle):
        name = self.handles[handle]
        self.calls.append(("ResetEvent", name))
        self.signaled[name] = False
        return 1

    def WaitForSingleObject(self, handle, timeout):
        name = self.handles[handle]
        script = self.wait_script.get(name, [])
        return script.pop(0) if script else WAIT_FAILED

    def CloseHandle(self, handle):
        self.closed.append(handle)
        return 1


def make(k32, **kw):
    return instance_mod.InstanceSignals(
        kernel32=k32, get_last_error=lambda: k32.last_error, **kw
    )


def join(signals):
    for t in signals._threads:
        t.join(timeout=2)
        assert not t.is_alive()


def test_first_instance_is_not_already_running():
    k32 = FakeKernel32()
    first = make(k32)
    assert first.already_running is False
    assert ("CreateMutexW", RUNNING_MUTEX_NAME) in k32.calls
    # O evento Show nasce junto com o mutex, com reset automático.
    assert ("CreateEventW", SHOW_EVENT_NAME, False) in k32.calls
    assert first.notify_existing() is False


def test_second_instance_detects_and_signals_show():
    k32 = FakeKernel32()
    make(k32)
    allowed = []
    second = make(k32, allow_foreground=lambda: allowed.append(True))
    assert second.already_running is True
    assert second.notify_existing() is True
    assert k32.signaled[SHOW_EVENT_NAME] is True
    assert ("SetEvent", SHOW_EVENT_NAME) in k32.calls
    assert allowed == [True]
    # A segunda não cria o evento Quit nem escuta nada.
    second.listen(lambda: None, lambda: None)
    assert second._threads == []
    assert not any(c[:2] == ("CreateEventW", QUIT_EVENT_NAME) for c in k32.calls)
    second.close()
    assert second._mutex is None


def test_notify_survives_allow_foreground_failure():
    k32 = FakeKernel32()
    make(k32)

    def boom():
        raise OSError("negado")

    second = make(k32, allow_foreground=boom)
    assert second.notify_existing() is True


def test_mutex_failure_runs_as_single_app():
    k32 = FakeKernel32()
    k32.fail_mutex = True
    signals = make(k32)
    assert signals.already_running is False
    signals.listen(lambda: None, lambda: None)  # não quebra sem evento Show
    signals.close()


def test_show_event_wakes_listener_many_times():
    k32 = FakeKernel32()
    signals = make(k32)
    k32.wait_script[SHOW_EVENT_NAME] = [0, 0, 0]  # três aberturas, depois falha
    shows, quits = [], []
    signals.listen(lambda: quits.append(1), lambda: shows.append(1))
    join(signals)
    assert shows == [1, 1, 1]
    assert quits == []


def test_show_listener_survives_callback_error():
    k32 = FakeKernel32()
    signals = make(k32)
    k32.wait_script[SHOW_EVENT_NAME] = [0, 0]
    calls = []

    def on_show():
        calls.append(1)
        raise RuntimeError("janela sumiu")

    signals.listen(lambda: None, on_show)
    join(signals)
    assert calls == [1, 1]


def test_quit_event_is_manual_reset_and_cleared_on_start():
    k32 = FakeKernel32()
    k32.names[QUIT_EVENT_NAME] = 1  # sobra de uma instalação anterior
    k32.signaled[QUIT_EVENT_NAME] = True
    k32.manual_reset[QUIT_EVENT_NAME] = True
    signals = make(k32)
    k32.wait_script[QUIT_EVENT_NAME] = [WAIT_FAILED]
    signals.listen(lambda: None, lambda: None)
    join(signals)
    assert ("CreateEventW", QUIT_EVENT_NAME, True) in k32.calls
    assert k32.signaled[QUIT_EVENT_NAME] is False


def test_quit_event_calls_on_quit():
    k32 = FakeKernel32()
    signals = make(k32)
    k32.wait_script[QUIT_EVENT_NAME] = [0]
    quits = []
    signals.listen(lambda: quits.append(1), lambda: None)
    join(signals)
    assert quits == [1]


def test_no_callbacks_after_close():
    k32 = FakeKernel32()
    signals = make(k32)
    signals.close()
    k32.wait_script[SHOW_EVENT_NAME] = [0]
    k32.wait_script[QUIT_EVENT_NAME] = [0]
    signals.listen(lambda: pytest.fail("quit"), lambda: pytest.fail("show"))
    assert signals._threads == []


def test_main_exits_early_when_already_running(monkeypatch):
    import pomodoro.__main__ as entry

    events = []

    class FakeSignals:
        already_running = True

        def notify_existing(self):
            events.append("notify")
            return True

        def close(self):
            events.append("close")

    monkeypatch.setattr(entry, "InstanceSignals", FakeSignals)
    monkeypatch.setattr(entry, "_run", lambda s: pytest.fail("não deveria abrir o app"))
    monkeypatch.setattr(entry, "load_config", lambda: pytest.fail("nem ler config"))
    monkeypatch.setattr(entry, "Storage", lambda: pytest.fail("nem abrir o banco"))
    entry.main()
    assert events == ["notify", "close"]


def test_main_runs_app_when_first(monkeypatch):
    import pomodoro.__main__ as entry

    events = []

    class FakeSignals:
        already_running = False

        def close(self):
            events.append("close")

    monkeypatch.setattr(entry, "InstanceSignals", FakeSignals)
    monkeypatch.setattr(entry, "_run", lambda s: events.append("run"))
    entry.main()
    assert events == ["run", "close"]
