"""Sinais nomeados do Windows para o instalador conseguir fechar o app aberto.

- Mutex ``PomodoroGatodoroRunning``: existe enquanto o app está aberto. O
  instalador usa CheckForMutexes para saber se precisa fechar algo.
- Evento ``PomodoroGatodoroQuit``: o instalador sinaliza; o app fecha como se o
  usuário tivesse escolhido "Sair" (grava o bloco em andamento, para a bandeja).

Os nomes precisam bater com packaging/pomodoro.iss. Fora do Windows é tudo no-op.
"""

from __future__ import annotations

import logging
import sys
import threading
from collections.abc import Callable

logger = logging.getLogger(__name__)

RUNNING_MUTEX_NAME = "PomodoroGatodoroRunning"
QUIT_EVENT_NAME = "PomodoroGatodoroQuit"

_INFINITE = 0xFFFFFFFF
_WAIT_OBJECT_0 = 0


class InstanceSignals:
    """Mantém o mutex e escuta o pedido de fechar. Chame close() ao sair."""

    def __init__(self, on_quit_requested: Callable[[], None]) -> None:
        self._on_quit = on_quit_requested
        self._kernel32 = None
        self._mutex = None
        self._event = None
        self._closed = False
        if sys.platform == "win32":
            try:
                self._open_windows()
            except Exception:
                logger.warning("Sinais de instância indisponíveis", exc_info=True)

    def _open_windows(self) -> None:  # pragma: no cover - só no Windows
        import ctypes
        from ctypes import wintypes

        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.CreateMutexW.restype = wintypes.HANDLE
        k32.CreateMutexW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
        k32.CreateEventW.restype = wintypes.HANDLE
        k32.CreateEventW.argtypes = (
            wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR,
        )
        k32.WaitForSingleObject.restype = wintypes.DWORD
        k32.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        k32.CloseHandle.argtypes = (wintypes.HANDLE,)
        self._kernel32 = k32

        self._mutex = k32.CreateMutexW(None, False, RUNNING_MUTEX_NAME)
        # Reset manual: um único SetEvent fecha todas as instâncias abertas.
        self._event = k32.CreateEventW(None, True, False, QUIT_EVENT_NAME)
        if not self._event:
            raise OSError(ctypes.get_last_error(), "CreateEventW falhou")
        # Se sobrou um evento sinalizado de uma instalação anterior (instância
        # travada que não fechou), não deixe o app recém-aberto fechar sozinho.
        k32.ResetEvent.argtypes = (wintypes.HANDLE,)
        k32.ResetEvent(self._event)
        threading.Thread(target=self._wait, name="quit-signal", daemon=True).start()

    def _wait(self) -> None:  # pragma: no cover - só no Windows
        k32, event = self._kernel32, self._event
        if k32 is None or event is None:
            return
        if k32.WaitForSingleObject(event, _INFINITE) == _WAIT_OBJECT_0 and not self._closed:
            logger.info("Pedido de fechar recebido (instalador)")
            self._on_quit()

    def close(self) -> None:
        """Libera o mutex ao sair, para o instalador ver que o app fechou."""
        self._closed = True
        k32 = self._kernel32
        if k32 is None:
            return
        # Só o mutex: fechar o evento com a thread esperando nele é comportamento
        # indefinido no Windows. O processo está saindo e o SO libera o resto.
        if self._mutex:  # pragma: no cover - só no Windows
            k32.CloseHandle(self._mutex)
            self._mutex = None
