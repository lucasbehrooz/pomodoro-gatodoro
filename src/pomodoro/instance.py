"""Sinais nomeados do Windows: instância única e fechamento pelo instalador.

- Mutex ``PomodoroGatodoroRunning``: existe enquanto o app está aberto. O
  instalador usa CheckForMutexes para saber se precisa fechar algo, e o próprio
  app usa ERROR_ALREADY_EXISTS para saber se já há outra instância aberta.
- Evento ``PomodoroGatodoroQuit``: o instalador sinaliza; o app fecha como se o
  usuário tivesse escolhido "Sair" (grava o bloco em andamento, para a bandeja).
- Evento ``PomodoroGatodoroShow``: uma segunda abertura sinaliza e sai; a
  instância original mostra a janela (mesmo se estava na bandeja).

Os nomes do mutex e do evento Quit precisam bater com packaging/pomodoro.iss.
Fora do Windows é tudo no-op: o app abre normalmente.
"""

from __future__ import annotations

import logging
import sys
import threading
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

RUNNING_MUTEX_NAME = "PomodoroGatodoroRunning"
QUIT_EVENT_NAME = "PomodoroGatodoroQuit"
SHOW_EVENT_NAME = "PomodoroGatodoroShow"

ERROR_ALREADY_EXISTS = 183
_INFINITE = 0xFFFFFFFF
_WAIT_OBJECT_0 = 0


def _load_kernel32() -> Any:  # pragma: no cover - só no Windows
    import ctypes
    from ctypes import wintypes

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateMutexW.restype = wintypes.HANDLE
    k32.CreateMutexW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
    k32.CreateEventW.restype = wintypes.HANDLE
    k32.CreateEventW.argtypes = (
        wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR,
    )
    k32.SetEvent.restype = wintypes.BOOL
    k32.SetEvent.argtypes = (wintypes.HANDLE,)
    k32.ResetEvent.restype = wintypes.BOOL
    k32.ResetEvent.argtypes = (wintypes.HANDLE,)
    k32.WaitForSingleObject.restype = wintypes.DWORD
    k32.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    k32.CloseHandle.argtypes = (wintypes.HANDLE,)
    return k32


def _allow_any_foreground() -> None:  # pragma: no cover - só no Windows
    """Deixa a instância original trazer a janela para frente.

    O Windows só deixa um processo roubar o foco se quem tem o foco permitir. A
    segunda abertura (que acabou de receber o clique do usuário) libera.
    """
    import ctypes

    asfw_any = -1
    ctypes.WinDLL("user32").AllowSetForegroundWindow(asfw_any)


class InstanceSignals:
    """Mantém o mutex, detecta outra instância e escuta os pedidos nomeados.

    Uso: crie no início do app (antes de janela e bandeja). Se ``already_running``,
    chame ``notify_existing()`` e saia. Senão, depois de montar a janela, chame
    ``listen(...)``. Chame ``close()`` ao sair.

    ``kernel32``, ``get_last_error`` e ``allow_foreground`` existem para os testes
    injetarem um kernel32 falso. Sem eles, fora do Windows tudo é no-op.
    """

    def __init__(
        self,
        *,
        kernel32: Any = None,
        get_last_error: Callable[[], int] | None = None,
        allow_foreground: Callable[[], None] | None = None,
    ) -> None:
        self._kernel32: Any = None
        self._get_last_error = get_last_error or (lambda: 0)
        self._allow_foreground = allow_foreground
        self._mutex: Any = None
        self._show_event: Any = None
        self._quit_event: Any = None
        self._already_running = False
        self._closed = False
        self._threads: list[threading.Thread] = []
        if kernel32 is None:
            if sys.platform != "win32":
                return
            try:  # pragma: no cover - só no Windows
                import ctypes

                kernel32 = _load_kernel32()
                self._get_last_error = ctypes.get_last_error
                self._allow_foreground = _allow_any_foreground
            except Exception:  # pragma: no cover - só no Windows
                logger.warning("Sinais de instância indisponíveis", exc_info=True)
                return
        self._kernel32 = kernel32
        try:
            self._acquire()
        except Exception:
            logger.warning("Falha ao verificar outra instância", exc_info=True)

    def _acquire(self) -> None:
        k32 = self._kernel32
        self._mutex = k32.CreateMutexW(None, False, RUNNING_MUTEX_NAME)
        # Ler o erro logo depois da chamada: é ele que diz se o mutex já existia.
        last_error = self._get_last_error()
        if not self._mutex:
            logger.warning("CreateMutexW falhou (erro %s); seguindo sem instância única", last_error)
            return
        self._already_running = last_error == ERROR_ALREADY_EXISTS
        if not self._already_running:
            # Reset automático: cada SetEvent acorda a espera uma vez e ela volta
            # a esperar, então dá para reabrir a janela quantas vezes quiser.
            self._show_event = k32.CreateEventW(None, False, False, SHOW_EVENT_NAME)

    @property
    def already_running(self) -> bool:
        """True se outra instância do app já estava aberta."""
        return self._already_running

    def notify_existing(self) -> bool:
        """Pede à instância já aberta que mostre a janela. True se o pedido saiu."""
        k32 = self._kernel32
        if k32 is None or not self._already_running:
            return False
        try:
            if self._allow_foreground is not None:
                try:
                    self._allow_foreground()
                except Exception:
                    logger.debug("AllowSetForegroundWindow falhou", exc_info=True)
            # CreateEventW abre o existente; se a outra instância ainda não o
            # criou, cria com os mesmos parâmetros e ela o encontra sinalizado.
            event = k32.CreateEventW(None, False, False, SHOW_EVENT_NAME)
            if not event:
                logger.warning("Não foi possível abrir o evento de mostrar a janela")
                return False
            ok = bool(k32.SetEvent(event))
            k32.CloseHandle(event)
            return ok
        except Exception:
            logger.warning("Falha ao avisar a instância aberta", exc_info=True)
            return False

    def listen(
        self,
        on_quit_requested: Callable[[], None],
        on_show_requested: Callable[[], None],
    ) -> None:
        """Escuta o instalador (fechar) e novas aberturas (mostrar) em threads daemon.

        Os callbacks rodam fora da thread do Tk: passe-os por ``window.post()``.
        """
        k32 = self._kernel32
        if k32 is None or self._already_running or self._closed:
            return
        try:
            # Reset manual: um único SetEvent fecha todas as instâncias abertas.
            self._quit_event = k32.CreateEventW(None, True, False, QUIT_EVENT_NAME)
            if self._quit_event:
                # Se sobrou um evento sinalizado de uma instalação anterior
                # (instância travada que não fechou), não feche o app recém-aberto.
                k32.ResetEvent(self._quit_event)
                self._start(self._wait_quit, on_quit_requested, "quit-signal")
            else:
                logger.warning("Evento de fechar indisponível (erro %s)", self._get_last_error())
            if self._show_event:
                self._start(self._wait_show, on_show_requested, "show-signal")
        except Exception:
            logger.warning("Falha ao escutar os sinais de instância", exc_info=True)

    def _start(self, target: Callable[[Callable[[], None]], None],
               callback: Callable[[], None], name: str) -> None:
        thread = threading.Thread(target=target, args=(callback,), name=name, daemon=True)
        self._threads.append(thread)
        thread.start()

    def _wait_quit(self, on_quit: Callable[[], None]) -> None:
        k32, event = self._kernel32, self._quit_event
        if k32.WaitForSingleObject(event, _INFINITE) == _WAIT_OBJECT_0 and not self._closed:
            logger.info("Pedido de fechar recebido (instalador)")
            on_quit()

    def _wait_show(self, on_show: Callable[[], None]) -> None:
        k32, event = self._kernel32, self._show_event
        while not self._closed:
            if k32.WaitForSingleObject(event, _INFINITE) != _WAIT_OBJECT_0:
                logger.warning("Espera do evento de mostrar falhou; parando de escutar")
                return
            if self._closed:
                return
            logger.info("Outra abertura pediu para mostrar a janela")
            try:
                on_show()
            except Exception:
                logger.exception("Falha ao mostrar a janela")

    def close(self) -> None:
        """Libera o mutex ao sair, para o instalador ver que o app fechou."""
        self._closed = True
        k32 = self._kernel32
        if k32 is None:
            return
        # Só o mutex: fechar um evento com a thread esperando nele é comportamento
        # indefinido no Windows. O processo está saindo e o SO libera o resto.
        if self._mutex:
            k32.CloseHandle(self._mutex)
            self._mutex = None
