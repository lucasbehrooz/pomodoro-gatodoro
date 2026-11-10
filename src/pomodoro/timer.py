"""Máquina de estados do Pomodoro. Sem dependência de GUI.

Contrato público:

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

Decisões de implementação:
- Em IDLE, remaining_seconds é a duração do foco (não 0).
- remaining_seconds é calculado ao vivo a partir do clock enquanto contando,
  sem mudar estado; o estado só muda em start/pause/tick/skip/reset.
- tick() processa no máximo UMA transição por chamada. Se o tempo passou de
  mais de um bloco, o excedente é descartado: o novo bloco começa com a
  duração cheia a partir do instante do tick. O timer continua rodando
  (avanço automático) após a transição.
- skip() preserva o estado de execução: se estava contando, o próximo bloco
  conta; se estava pausado, o próximo bloco começa pausado com duração cheia.
  Em IDLE, skip() é no-op.
- skip() em LONG_BREAK também zera completed_focus_count, pois encerra o ciclo
  (senão o próximo foco disparava pausa longa de novo imediatamente).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from pomodoro.config import Config


class Phase(Enum):
    IDLE = "idle"
    FOCUS = "focus"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


@dataclass(frozen=True)
class TransitionEvent:
    finished: Phase
    next: Phase


class PomodoroTimer:
    def __init__(self, config: Config, clock: Callable[[], float] = time.monotonic) -> None:
        self._config = config
        self._clock = clock
        self._phase = Phase.IDLE
        self._running = False
        self._remaining = self._duration(Phase.FOCUS)
        # Instante do clock em que o trecho de contagem atual começou.
        self._segment_start = 0.0
        self._completed_focus_count = 0

    # ---- propriedades -------------------------------------------------

    @property
    def phase(self) -> Phase:
        return self._phase

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def remaining_seconds(self) -> float:
        if self._running:
            elapsed = self._clock() - self._segment_start
            return max(0.0, self._remaining - elapsed)
        return self._remaining

    @property
    def completed_focus_count(self) -> int:
        return self._completed_focus_count

    # ---- comandos -----------------------------------------------------

    def start(self) -> None:
        if self._running:
            return
        if self._phase is Phase.IDLE:
            self._phase = Phase.FOCUS
            self._remaining = self._duration(Phase.FOCUS)
        self._running = True
        self._segment_start = self._clock()

    def pause(self) -> None:
        if not self._running:
            return
        self._sync()
        self._running = False

    def reset(self) -> None:
        self._phase = Phase.IDLE
        self._running = False
        self._remaining = self._duration(Phase.FOCUS)
        self._completed_focus_count = 0

    def skip(self) -> None:
        if self._phase is Phase.IDLE:
            return
        current = self._phase
        if current is Phase.FOCUS:
            # Pular foco não conta como foco concluído.
            nxt = self._break_after_focus()
        elif current is Phase.SHORT_BREAK:
            nxt = Phase.FOCUS
        else:  # LONG_BREAK encerra o ciclo
            self._completed_focus_count = 0
            nxt = Phase.FOCUS
        self._enter(nxt)

    def tick(self) -> Optional[TransitionEvent]:
        if not self._running:
            return None
        self._sync()
        if self._remaining > 0:
            return None
        finished = self._phase
        if finished is Phase.FOCUS:
            self._completed_focus_count += 1
            nxt = self._break_after_focus()
        elif finished is Phase.SHORT_BREAK:
            nxt = Phase.FOCUS
        else:  # LONG_BREAK
            self._completed_focus_count = 0
            nxt = Phase.FOCUS
        self._enter(nxt)
        return TransitionEvent(finished=finished, next=nxt)

    # ---- internos -----------------------------------------------------

    def _sync(self) -> None:
        """Desconta do restante o tempo decorrido desde o último ponto de contagem."""
        now = self._clock()
        self._remaining -= now - self._segment_start
        self._segment_start = now

    def _enter(self, phase: Phase) -> None:
        """Entra em um novo bloco com duração cheia, a partir de agora."""
        self._phase = phase
        self._remaining = self._duration(phase)
        self._segment_start = self._clock()

    def _break_after_focus(self) -> Phase:
        if self._completed_focus_count >= self._config.cycles_before_long_break:
            return Phase.LONG_BREAK
        return Phase.SHORT_BREAK

    def _duration(self, phase: Phase) -> float:
        cfg = self._config
        minutes = {
            Phase.IDLE: cfg.focus_minutes,
            Phase.FOCUS: cfg.focus_minutes,
            Phase.SHORT_BREAK: cfg.short_break_minutes,
            Phase.LONG_BREAK: cfg.long_break_minutes,
        }[phase]
        return float(minutes * 60)
