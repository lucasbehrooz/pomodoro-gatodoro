"""Interface de notificações. Implementações concretas ficam na Fase 5.

Contrato:

    class Notifier(Protocol):
        def alert_sound(self) -> None           # toca o som de alerta
        def toast(self, title: str, message: str) -> None   # notificação do Windows

Implementações previstas:
    - WindowsNotifier: winsound + winotify (Fase 5)
    - NullNotifier: no-op, para testes e outros sistemas operacionais
"""

from __future__ import annotations

import logging
import sys
from typing import Protocol

logger = logging.getLogger(__name__)

# Som de alerta: alias "SystemAsterisk" (som de Asterisco do esquema de sons
# do Windows). PlaySound com SND_ALIAS | SND_ASYNC retorna imediatamente e
# respeita o esquema de sons escolhido pelo usuário.
SYSTEM_ALERT_SOUND = "SystemAsterisk"


class Notifier(Protocol):
    def alert_sound(self) -> None: ...

    def toast(self, title: str, message: str) -> None: ...


class NullNotifier:
    """No-op. Usado em testes e fora do Windows."""

    def alert_sound(self) -> None:
        return None

    def toast(self, title: str, message: str) -> None:
        return None


class WindowsNotifier:
    """Som via winsound e notificação toast via winotify.

    Imports são lazy: winsound e winotify só existem no Windows. Falhas são
    registradas em log e nunca propagam para o app.
    """

    def __init__(
        self,
        app_id: str = "Pomodoro Gatodoro",
        sound_enabled: bool = True,
        toast_enabled: bool = True,
    ) -> None:
        self.app_id = app_id
        self.sound_enabled = sound_enabled
        self.toast_enabled = toast_enabled

    def alert_sound(self) -> None:
        if not self.sound_enabled:
            return
        try:
            import winsound

            winsound.PlaySound(
                SYSTEM_ALERT_SOUND,
                winsound.SND_ALIAS | winsound.SND_ASYNC,
            )
        except Exception:
            logger.warning("Falha ao tocar som de alerta", exc_info=True)

    def toast(self, title: str, message: str) -> None:
        if not self.toast_enabled:
            return
        try:
            from winotify import Notification

            Notification(app_id=self.app_id, title=title, msg=message).show()
        except Exception:
            logger.warning("Falha ao exibir notificação toast", exc_info=True)


def get_notifier(sound_enabled: bool, toast_enabled: bool) -> Notifier:
    """WindowsNotifier no Windows; NullNotifier nos demais sistemas."""
    if sys.platform == "win32":
        return WindowsNotifier(sound_enabled=sound_enabled, toast_enabled=toast_enabled)
    return NullNotifier()
