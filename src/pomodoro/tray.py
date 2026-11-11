"""Ícone na bandeja do sistema (pystray + Pillow). Desacoplado da UI Tk.

Contrato público:

    class TrayIcon:
        def __init__(on_toggle, on_show, on_quit, title="Pomodoro")
        is_available: bool          # False se a bandeja não pôde ser iniciada
        events: queue.Queue         # fila de ("toggle" | "show" | "quit")

        def start() -> None         # sobe o ícone em thread daemon própria
        def stop() -> None          # para o ícone; idempotente
        def set_status(text, running) -> None   # thread-safe
        def poll() -> int           # executa callbacks pendentes; retorna quantos

Modelo de threads:

- pystray bloqueia em Icon.run(), por isso roda em thread daemon. Os itens de
  menu dessa thread NÃO chamam callbacks: só colocam o nome do evento em
  ``self.events``.
- A UI (thread do Tk) deve chamar ``tray.poll()`` periodicamente, por exemplo
  via ``root.after(100, ...)``. É nesse momento que os callbacks on_toggle,
  on_show e on_quit são executados, na thread chamadora. Assim nenhum callback
  toca widgets Tk a partir de outra thread.

pystray e PIL são importados de forma lazy, então o módulo importa em qualquer
sistema sem display.
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)

ICON_SIZE = 64
_RED = (200, 40, 40, 255)
_WHITE = (255, 255, 255, 255)

EVENT_TOGGLE = "toggle"
EVENT_SHOW = "show"
EVENT_QUIT = "quit"


def make_icon(running: bool = False) -> Any:
    """Ícone 64x64 da bandeja: gato (assets/gato.png) com ponto branco ao rodar.

    Sem o arquivo, usa o círculo vermelho de reserva.
    """
    from PIL import Image, ImageDraw

    from pomodoro.assets import ICON_PNG_PATH

    if ICON_PNG_PATH.exists():
        image = Image.open(ICON_PNG_PATH).convert("RGBA").resize((ICON_SIZE, ICON_SIZE))
        if running:
            draw = ImageDraw.Draw(image)
            draw.ellipse((ICON_SIZE - 20, ICON_SIZE - 20, ICON_SIZE - 3, ICON_SIZE - 3), fill=_RED, outline=_WHITE, width=2)
        return image

    image = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((4, 4, ICON_SIZE - 5, ICON_SIZE - 5), fill=_RED)
    if running:
        draw.ellipse((22, 22, 41, 41), fill=_WHITE)
    return image


class TrayIcon:
    def __init__(
        self,
        on_toggle: Callable[[], None],
        on_show: Callable[[], None],
        on_quit: Callable[[], None],
        title: str = "Pomodoro",
    ) -> None:
        self._callbacks: dict[str, Callable[[], None]] = {
            EVENT_TOGGLE: on_toggle,
            EVENT_SHOW: on_show,
            EVENT_QUIT: on_quit,
        }
        self._title = title
        self.events: queue.Queue[str] = queue.Queue()
        self.is_available = False

        self._lock = threading.Lock()
        self._icon: Any = None
        self._thread: Optional[threading.Thread] = None
        self._status_text = title
        self._running = False
        self._images: dict[bool, Any] = {}

    # ---- ciclo de vida ------------------------------------------------

    def start(self) -> None:
        """Cria o ícone e o executa em thread daemon. Falhas são registradas, não propagadas."""
        with self._lock:
            if self._icon is not None:
                return
            try:
                import pystray

                icon = pystray.Icon(
                    "pomodoro",
                    icon=self._icon_image(self._running),
                    title=self._status_text,
                    menu=self._build_menu(pystray),
                )
            except Exception:
                log.warning("Bandeja do sistema indisponível", exc_info=True)
                self.is_available = False
                return
            self._icon = icon
            self._thread = threading.Thread(
                target=self._run_icon, args=(icon,), name="pomodoro-tray", daemon=True
            )
            self.is_available = True
            self._thread.start()

    def stop(self) -> None:
        """Para o ícone e encerra a thread. Chamadas repetidas não fazem nada."""
        with self._lock:
            icon, thread = self._icon, self._thread
            self._icon = None
            self._thread = None
        if icon is None:
            return
        try:
            icon.stop()
        except Exception:
            log.debug("Erro ao parar o ícone da bandeja", exc_info=True)
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2.0)

    # ---- estado -------------------------------------------------------

    def set_status(self, text: str, running: bool) -> None:
        """Atualiza tooltip e ícone. Seguro em qualquer thread.

        Se o ícone ainda não existe, o estado é guardado e aplicado em start().
        """
        with self._lock:
            self._status_text = text
            self._running = running
            icon = self._icon
            image = self._icon_image(running) if icon is not None else None
        if icon is None:
            return
        try:
            icon.title = text
            icon.icon = image
        except Exception:
            log.debug("Falha ao atualizar o ícone da bandeja", exc_info=True)

    # ---- despacho para a UI -------------------------------------------

    def poll(self) -> int:
        """Executa os callbacks pendentes na thread chamadora. Retorna quantos rodaram.

        Deve ser chamado pela thread da UI. Erros em um callback são registrados
        e não impedem os demais.
        """
        handled = 0
        while True:
            try:
                name = self.events.get_nowait()
            except queue.Empty:
                return handled
            callback = self._callbacks.get(name)
            if callback is None:
                log.warning("Evento desconhecido da bandeja: %r", name)
                continue
            handled += 1
            try:
                callback()
            except Exception:
                log.exception("Erro no callback da bandeja (%s)", name)

    # ---- internos -----------------------------------------------------

    def _build_menu(self, pystray: Any) -> Any:
        return pystray.Menu(
            pystray.MenuItem("Iniciar/Pausar", lambda icon, item: self.events.put(EVENT_TOGGLE)),
            pystray.MenuItem(
                "Abrir", lambda icon, item: self.events.put(EVENT_SHOW), default=True
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Sair", lambda icon, item: self.events.put(EVENT_QUIT)),
        )

    def _icon_image(self, running: bool) -> Any:
        # Chamado com self._lock já adquirido; cache evita regerar a imagem.
        if running not in self._images:
            self._images[running] = make_icon(running)
        return self._images[running]

    def _run_icon(self, icon: Any) -> None:
        try:
            icon.run()
        except Exception:
            log.warning("Bandeja do sistema falhou durante a execução", exc_info=True)
            self.is_available = False
