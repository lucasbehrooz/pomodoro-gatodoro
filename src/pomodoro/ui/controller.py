"""Controlador da UI principal. Sem dependência de widgets (testável sem display).

A janela traduz eventos de usuário e de tick em chamadas a este controlador.
Efeitos colaterais: Storage (sessões), Notifier (som/toast) e player de ruído
(opcional, injetado).

Regras de registro de sessões:
- Bloco concluído (tick com transição): completed=True, duração planejada.
- Bloco interrompido por skip/reset/shutdown: completed=False, duração
  decorrida. Blocos sem nenhum segundo decorrido não são gravados.
- Pausar não encerra o bloco.

Meta diária (``Config.daily_goal``, 0 = desligada):
- A contagem do dia vem do Storage (focos concluídos com dia local de hoje).
- A comemoração dispara quando um foco concluído faz a contagem do dia
  cruzar a meta (antes < meta <= depois). Como a contagem só cresce ao longo
  do dia, isso acontece uma vez por dia e sobrevive a reinícios do app sem
  gravar nada extra. Um guarda em memória evita repetir no mesmo dia se o
  usuário mudar a meta depois de batê-la.
"""

from __future__ import annotations

import logging
import math
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional, Protocol

from pomodoro.config import Config
from pomodoro.notifier import Notifier, NullNotifier
from pomodoro.storage import Storage
from pomodoro.timer import Phase, PomodoroTimer, TransitionEvent

logger = logging.getLogger(__name__)

NOISE_FADE_SECONDS = 1.0
ALERT_PAUSE_SECONDS = 3.0

TOAST_TITLE = "Pomodoro Gatodoro"
NEXT_STEP_MESSAGES: dict[Phase, str] = {
    Phase.FOCUS: "Hora de focar",
    Phase.SHORT_BREAK: "Hora da pausa",
    Phase.LONG_BREAK: "Hora da pausa longa",
}

GOAL_REACHED_MESSAGE = "Meta do dia batida: {goal} pomodoros! Bom trabalho."

PHASE_LABELS: dict[Phase, str] = {
    Phase.IDLE: "Ocioso",
    Phase.FOCUS: "Foco",
    Phase.SHORT_BREAK: "Pausa curta",
    Phase.LONG_BREAK: "Pausa longa",
}

# Campos que afetam a máquina de estados do timer (recriação do PomodoroTimer).
TIMER_FIELDS: tuple[str, ...] = (
    "focus_minutes",
    "short_break_minutes",
    "long_break_minutes",
    "cycles_before_long_break",
)


class NoiseControl(Protocol):
    """Interface mínima do player de ruído (entregue pelo módulo noise)."""

    def start(self, fade_seconds: float) -> None: ...

    def stop(self, fade_seconds: float) -> None: ...

    def set_volume(self, volume: float) -> None: ...

    def pause_for_alert(self, seconds: float) -> None: ...


class ApplyStatus(Enum):
    """Resultado de apply_config, referente às durações/ciclos do timer.

    APPLIED: o timer já usa a configuração nova.
    DEFERRED: há bloco em andamento; durações/ciclos aguardam o próximo Reiniciar.
    Campos que não afetam o timer (som, toast, ruído, bandeja) são sempre
    aplicados imediatamente.
    """

    APPLIED = "applied"
    DEFERRED = "deferred"


def format_mmss(seconds: float) -> str:
    total = max(0, math.ceil(seconds))
    minutes, secs = divmod(total, 60)
    return f"{minutes:02d}:{secs:02d}"


def goal_progress_text(count: int, goal: int) -> str:
    """Texto da tela inicial: 'Hoje: 3/8'. Meta 0 (desligada) não mostra nada."""
    if goal <= 0:
        return ""
    text = f"Hoje: {count}/{goal}"
    if count >= goal:
        text += " · meta batida"
    return text


def goal_just_reached(before: int, after: int, goal: int) -> bool:
    """True quando a contagem do dia passou de abaixo da meta para a meta ou além."""
    return goal > 0 and before < goal <= after


def _timer_fields(config: Config) -> tuple[int, ...]:
    return tuple(getattr(config, name) for name in TIMER_FIELDS)


class PomodoroController:
    def __init__(
        self,
        config: Config,
        storage: Storage,
        notifier: Optional[Notifier] = None,
        noise_player: Optional[NoiseControl] = None,
        *,
        notifier_factory: Optional[Callable[[Config], Notifier]] = None,
        clock: Callable[[], float] = time.monotonic,
        now: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._config = config
        self._timer_config = config
        self._storage = storage
        self._notifier: Notifier = notifier or NullNotifier()
        self._notifier_factory = notifier_factory
        self._noise = noise_player
        self._clock = clock
        self._now = now
        self._timer = PomodoroTimer(config, clock)
        self._timer_config_pending: Optional[Config] = None
        # Instante de início do bloco atual, só após o bloco começar a contar.
        self._block_started_at: Optional[datetime] = None
        self._noise_on = False
        # Focos concluídos hoje: (dia local, contagem). None força nova consulta.
        # Contagem None = consulta falhou (desconhecida): a tela mostra 0 e não há comemoração.
        self._today_cache: Optional[tuple[date, Optional[int]]] = None
        self._goal_celebrated_on: Optional[date] = None

    # ---- estado para a UI -----------------------------------------------

    @property
    def config(self) -> Config:
        return self._config

    @property
    def phase(self) -> Phase:
        return self._timer.phase

    @property
    def phase_label(self) -> str:
        return PHASE_LABELS[self._timer.phase]

    @property
    def is_running(self) -> bool:
        return self._timer.is_running

    @property
    def remaining_seconds(self) -> float:
        return self._timer.remaining_seconds

    @property
    def completed_focus_count(self) -> int:
        return self._timer.completed_focus_count

    @property
    def cycles_before_long_break(self) -> int:
        return self._timer_config.cycles_before_long_break

    @property
    def timer_config_pending(self) -> bool:
        return self._timer_config_pending is not None

    @property
    def noise_playing(self) -> bool:
        return self._noise_on

    @property
    def today_focus_count(self) -> int:
        """Focos concluídos hoje (dia local); 0 se a consulta falhou."""
        count = self._today_count_or_none()
        return 0 if count is None else count

    def _today_count_or_none(self) -> Optional[int]:
        """Contagem do dia com cache até o próximo registro ou virada do dia.

        None quando a consulta falhou. A falha também fica em cache, para não
        repetir a consulta (e o log) a cada tick.
        """
        today = self._now().date()
        cached = self._today_cache
        if cached is not None and cached[0] == today:
            return cached[1]
        count: Optional[int]
        try:
            count = self._storage.count_completed_focus(today)
        except Exception:
            logger.exception("Falha ao contar os focos de hoje")
            count = None
        self._today_cache = (today, count)
        return count

    @property
    def daily_goal_text(self) -> str:
        """'Hoje: 3/8' para a tela inicial; vazio com a meta desligada."""
        goal = self._config.daily_goal
        if goal <= 0:
            return ""
        return goal_progress_text(self.today_focus_count, goal)

    # ---- comandos -------------------------------------------------------

    def start(self) -> None:
        if self._timer.is_running:
            return
        self._timer.start()
        if self._block_started_at is None and self._timer.phase is not Phase.IDLE:
            self._block_started_at = self._now()
        self._sync_noise()

    def pause(self) -> None:
        if not self._timer.is_running:
            return
        self._timer.pause()
        self._sync_noise()

    def toggle(self) -> None:
        if self._timer.is_running:
            self.pause()
        else:
            self.start()

    def reset(self) -> None:
        self._end_block()
        self._timer.reset()
        self._apply_pending_timer_config()
        self._sync_noise()

    def skip(self) -> None:
        if self._timer.phase is Phase.IDLE:
            return
        self._end_block()
        self._timer.skip()
        if self._timer.is_running:
            self._block_started_at = self._now()
        self._sync_noise()

    def tick(self) -> Optional[TransitionEvent]:
        event = self._timer.tick()
        if event is None:
            return None

        finished_started = self._block_started_at
        # O próximo bloco começa contando imediatamente neste instante.
        self._block_started_at = self._now()
        check_goal = event.finished is Phase.FOCUS and finished_started is not None
        goal_before = self._today_count_or_none() if check_goal else None
        if finished_started is not None:
            self._record(
                event.finished,
                finished_started,
                self._planned_seconds(event.finished),
                completed=True,
            )
        else:
            logger.warning("Bloco %s concluído sem início registrado", event.finished)

        self._sync_noise()
        self._notify_transition(event)
        if check_goal:
            self._maybe_celebrate_goal(goal_before)
        return event

    def apply_config(self, new: Config) -> ApplyStatus:
        """Aplica uma nova configuração sem reiniciar o app.

        O chamador deve persistir a configuração (save_config) antes.
        """
        noise = self._noise
        if self._noise_on and noise is not None:
            volume = new.brown_noise_volume
            self._call("ruído (volume)", lambda: noise.set_volume(volume))

        self._config = new
        if self._notifier_factory is not None:
            self._notifier = self._notifier_factory(new)

        status = ApplyStatus.APPLIED
        if _timer_fields(new) == _timer_fields(self._timer_config):
            self._timer_config_pending = None
        elif self._timer.phase is Phase.IDLE:
            self._use_timer_config(new)
        else:
            self._timer_config_pending = new
            status = ApplyStatus.DEFERRED

        self._sync_noise()
        return status

    def shutdown(self) -> None:
        """Encerra o app: registra o bloco em andamento como interrompido."""
        self._end_block()
        self._stop_noise()

    # ---- internos: sessões ----------------------------------------------

    def _planned_seconds(self, phase: Phase) -> int:
        cfg = self._timer_config
        minutes = {
            Phase.FOCUS: cfg.focus_minutes,
            Phase.SHORT_BREAK: cfg.short_break_minutes,
            Phase.LONG_BREAK: cfg.long_break_minutes,
        }.get(phase, 0)
        return minutes * 60

    def _end_block(self) -> None:
        """Encerra o bloco atual como interrompido, se ele chegou a contar."""
        started = self._block_started_at
        phase = self._timer.phase
        self._block_started_at = None
        if started is None or phase is Phase.IDLE:
            return
        elapsed = self._planned_seconds(phase) - self._timer.remaining_seconds
        seconds = max(0, int(elapsed))
        if seconds < 1:
            return
        self._record(phase, started, seconds, completed=False)

    def _record(self, phase: Phase, started_at: datetime, seconds: int, completed: bool) -> None:
        self._today_cache = None
        task = self._config.current_task or None
        self._call(
            "registro da sessão",
            lambda: self._storage.record_session(phase, started_at, seconds, completed, task),
        )

    # ---- internos: notificações -----------------------------------------

    def _notify_transition(self, event: TransitionEvent) -> None:
        if self._config.sound_enabled:
            self._call("alerta sonoro", self._notifier.alert_sound)
            if self._noise_on and self._noise is not None:
                noise = self._noise
                self._call(
                    "ruído (pausa para alerta)",
                    lambda: noise.pause_for_alert(ALERT_PAUSE_SECONDS),
                )
        if self._config.toast_enabled:
            message = NEXT_STEP_MESSAGES[event.next]
            self._call("toast", lambda: self._notifier.toast(TOAST_TITLE, message))

    def _maybe_celebrate_goal(self, before: Optional[int]) -> None:
        """Comemora a meta diária quando o foco recém-gravado a alcança (uma vez por dia).

        Contagem desconhecida (falha do banco) antes ou depois não comemora:
        sem saber o valor anterior, a meta pode já ter sido batida.
        """
        goal = self._config.daily_goal
        today = self._now().date()
        if self._goal_celebrated_on == today or before is None:
            return
        after = self._today_count_or_none()
        if after is None or not goal_just_reached(before, after, goal):
            return
        self._goal_celebrated_on = today
        if self._config.toast_enabled:
            message = GOAL_REACHED_MESSAGE.format(goal=goal)
            self._call("toast (meta diária)", lambda: self._notifier.toast(TOAST_TITLE, message))

    # ---- internos: ruído ------------------------------------------------

    def _noise_allowed(self) -> bool:
        cfg = self._config
        if not cfg.brown_noise_enabled or not self._timer.is_running:
            return False
        phase = self._timer.phase
        if phase is Phase.FOCUS:
            return True
        if phase in (Phase.SHORT_BREAK, Phase.LONG_BREAK):
            return not cfg.brown_noise_focus_only
        return False

    def _sync_noise(self) -> None:
        if self._noise_allowed():
            if not self._noise_on and self._noise is not None:
                self._start_noise(self._noise)
        else:
            self._stop_noise()

    def _start_noise(self, noise: NoiseControl) -> None:
        volume = self._config.brown_noise_volume

        def run() -> None:
            noise.set_volume(volume)
            noise.start(NOISE_FADE_SECONDS)

        self._noise_on = self._call("ruído (start)", run)

    def _stop_noise(self) -> None:
        if not self._noise_on:
            return
        self._noise_on = False
        if self._noise is not None:
            noise = self._noise
            self._call("ruído (stop)", lambda: noise.stop(NOISE_FADE_SECONDS))

    # ---- internos: configuração do timer --------------------------------

    def _use_timer_config(self, cfg: Config) -> None:
        self._timer_config = cfg
        self._timer = PomodoroTimer(cfg, self._clock)
        self._timer_config_pending = None

    def _apply_pending_timer_config(self) -> None:
        pending = self._timer_config_pending
        if pending is not None and self._timer.phase is Phase.IDLE:
            self._use_timer_config(pending)

    # ---- util -----------------------------------------------------------

    def _call(self, what: str, fn: Callable[[], object]) -> bool:
        """Executa um efeito colateral; falhas são logadas e nunca quebram o timer."""
        try:
            fn()
        except Exception:
            logger.exception("Falha em %s; o timer segue funcionando", what)
            return False
        return True
