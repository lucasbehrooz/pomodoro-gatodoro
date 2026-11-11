"""Iniciar com o Windows: grava/remove o valor "Pomodoro" em HKCU\\...\\Run.

Usa HKCU, então não exige administrador. Fora do Windows, ou sem winreg
disponível, as funções não fazem nada e apenas registram log.

O registro é injetável (``registry=``) para os testes. Um registro é um objeto
com os métodos:

    get_value(name) -> str | None
    set_value(name, command) -> None
    delete_value(name) -> None   (sem erro se o valor não existir)

Erros reais do registro (OSError) são propagados para quem chama, que decide
como mostrar ao usuário.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Protocol

logger = logging.getLogger(__name__)

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "Pomodoro"


class RunRegistry(Protocol):
    def get_value(self, name: str) -> str | None: ...
    def set_value(self, name: str, command: str) -> None: ...
    def delete_value(self, name: str) -> None: ...


def command_for_autostart() -> str:
    """Linha de comando gravada no registro.

    No executável do PyInstaller (sys.frozen), o próprio .exe. Em desenvolvimento,
    o interpretador atual com ``-m pomodoro``. Caminhos vão entre aspas.
    """
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    return f'"{sys.executable}" -m pomodoro'


class _WinRegistry:
    """Adaptador sobre winreg. Só é criado em win32."""

    def __init__(self, winreg: Any) -> None:
        self._winreg = winreg

    def get_value(self, name: str) -> str | None:
        wr = self._winreg
        try:
            with wr.OpenKey(wr.HKEY_CURRENT_USER, RUN_KEY, 0, wr.KEY_READ) as key:
                value, _ = wr.QueryValueEx(key, name)
        except FileNotFoundError:
            return None
        return str(value)

    def set_value(self, name: str, command: str) -> None:
        wr = self._winreg
        with wr.OpenKey(wr.HKEY_CURRENT_USER, RUN_KEY, 0, wr.KEY_SET_VALUE) as key:
            wr.SetValueEx(key, name, 0, wr.REG_SZ, command)

    def delete_value(self, name: str) -> None:
        wr = self._winreg
        try:
            with wr.OpenKey(wr.HKEY_CURRENT_USER, RUN_KEY, 0, wr.KEY_SET_VALUE) as key:
                wr.DeleteValue(key, name)
        except FileNotFoundError:
            pass


def default_registry() -> RunRegistry | None:
    """Registro real do Windows, ou None fora do Windows / sem winreg."""
    if sys.platform != "win32":
        return None
    try:
        import winreg
    except ImportError:
        logger.warning("winreg indisponível; 'Iniciar com o Windows' não será aplicado")
        return None
    return _WinRegistry(winreg)


def set_autostart(enabled: bool, registry: RunRegistry | None = None) -> None:
    """Liga ou desliga a inicialização com o Windows.

    Sem registro disponível (Linux, por exemplo), não faz nada e registra log.
    """
    reg = registry if registry is not None else default_registry()
    if reg is None:
        logger.info("Autostart ignorado: registro do Windows indisponível (enabled=%s)", enabled)
        return
    if enabled:
        reg.set_value(VALUE_NAME, command_for_autostart())
    else:
        reg.delete_value(VALUE_NAME)


def is_autostart_enabled(registry: RunRegistry | None = None) -> bool:
    """True se o valor "Pomodoro" existe no registro. False se não houver registro."""
    reg = registry if registry is not None else default_registry()
    if reg is None:
        return False
    return reg.get_value(VALUE_NAME) is not None
