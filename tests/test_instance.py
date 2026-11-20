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
    signals = InstanceSignals(lambda: called.append(True))
    signals.close()
    signals.close()  # idempotente
    assert called == []
