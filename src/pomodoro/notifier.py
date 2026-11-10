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

from typing import Protocol


class Notifier(Protocol):
    def alert_sound(self) -> None: ...

    def toast(self, title: str, message: str) -> None: ...


class NullNotifier:
    """No-op. Usado em testes e fora do Windows."""

    def alert_sound(self) -> None:
        return None

    def toast(self, title: str, message: str) -> None:
        return None
