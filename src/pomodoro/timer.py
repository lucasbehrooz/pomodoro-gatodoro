"""Máquina de estados do Pomodoro. Sem dependência de GUI.

Contrato público (a ser implementado na Fase 1):

    class Phase(Enum):
        IDLE, FOCUS, SHORT_BREAK, LONG_BREAK

    class PomodoroTimer:
        def __init__(self, config: Config, clock: Callable[[], float] = time.monotonic)
        phase: Phase                 # fase atual
        is_running: bool             # True se contando (não pausado)
        remaining_seconds: float     # tempo restante no bloco atual
        completed_focus_count: int   # focos concluídos no ciclo atual

        def start() -> None          # inicia ou retoma; em IDLE começa FOCUS
        def pause() -> None
        def reset() -> None          # volta para IDLE
        def skip() -> None           # encerra o bloco atual e avança
        def tick() -> Optional[TransitionEvent]
            # chamado periodicamente pela UI; retorna evento ao completar um bloco

    @dataclass
    class TransitionEvent:
        finished: Phase              # bloco que terminou
        next: Phase                  # próximo bloco

Regra: a contagem usa o clock injetado, nunca sleep().
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Phase(Enum):
    IDLE = "idle"
    FOCUS = "focus"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


@dataclass(frozen=True)
class TransitionEvent:
    finished: Phase
    next: Phase
