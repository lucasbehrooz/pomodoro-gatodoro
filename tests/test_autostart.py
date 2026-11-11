import logging
import sys

import pytest

from pomodoro import autostart
from pomodoro.autostart import (
    VALUE_NAME,
    command_for_autostart,
    is_autostart_enabled,
    set_autostart,
)


class FakeRegistry:
    def __init__(self, fail_with: Exception | None = None) -> None:
        self.values: dict[str, str] = {}
        self.fail_with = fail_with

    def _check(self) -> None:
        if self.fail_with is not None:
            raise self.fail_with

    def get_value(self, name):
        self._check()
        return self.values.get(name)

    def set_value(self, name, command):
        self._check()
        self.values[name] = command

    def delete_value(self, name):
        self._check()
        self.values.pop(name, None)


def test_command_in_development_uses_module(monkeypatch):
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\Python311\python.exe")
    assert command_for_autostart() == '"C:\\Python311\\python.exe" -m pomodoro'


def test_command_frozen_is_quoted_executable(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\Program Files\Pomodoro\Pomodoro.exe")
    assert command_for_autostart() == '"C:\\Program Files\\Pomodoro\\Pomodoro.exe"'


def test_enable_writes_value_and_is_enabled():
    reg = FakeRegistry()
    set_autostart(True, registry=reg)
    assert VALUE_NAME in reg.values
    assert reg.values[VALUE_NAME] == command_for_autostart()
    assert is_autostart_enabled(registry=reg) is True


def test_disable_removes_value():
    reg = FakeRegistry()
    set_autostart(True, registry=reg)
    set_autostart(False, registry=reg)
    assert VALUE_NAME not in reg.values
    assert is_autostart_enabled(registry=reg) is False


def test_disable_when_absent_does_not_fail():
    reg = FakeRegistry()
    set_autostart(False, registry=reg)
    assert reg.values == {}


def test_enable_twice_overwrites_with_current_command(monkeypatch):
    reg = FakeRegistry()
    reg.values[VALUE_NAME] = '"C:\\antigo\\Pomodoro.exe"'
    set_autostart(True, registry=reg)
    assert reg.values[VALUE_NAME] == command_for_autostart()


def test_is_enabled_false_when_absent():
    assert is_autostart_enabled(registry=FakeRegistry()) is False


def test_registry_errors_propagate_to_caller():
    reg = FakeRegistry(fail_with=PermissionError("negado"))
    with pytest.raises(PermissionError):
        set_autostart(True, registry=reg)


def test_without_registry_is_noop_and_logs(monkeypatch, caplog):
    monkeypatch.setattr(autostart, "default_registry", lambda: None)
    with caplog.at_level(logging.INFO, logger="pomodoro.autostart"):
        set_autostart(True)  # não levanta
    assert is_autostart_enabled() is False
    assert any("indisponível" in r.message for r in caplog.records)


def test_default_registry_none_outside_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert autostart.default_registry() is None


def test_default_registry_none_without_winreg(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "winreg", None)  # força ImportError
    assert autostart.default_registry() is None
