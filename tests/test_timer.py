from __future__ import annotations

import time

import pytest

from pomodoro.config import Config
from pomodoro.timer import Phase, PomodoroTimer, TransitionEvent


class FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def no_sleep(monkeypatch):
    """Garante que o timer nunca bloqueia com sleep()."""

    def _forbidden(*_args, **_kwargs):
        raise AssertionError("time.sleep não deve ser usado pelo timer")

    monkeypatch.setattr(time, "sleep", _forbidden)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def config() -> Config:
    # Durações de 1 minuto (60 s) para facilitar as contas dos testes.
    return Config(
        focus_minutes=1,
        short_break_minutes=1,
        long_break_minutes=2,
        cycles_before_long_break=2,
    )


@pytest.fixture
def timer(config, clock) -> PomodoroTimer:
    return PomodoroTimer(config, clock=clock)


# ---- estado inicial ----------------------------------------------------


def test_initial_state_is_idle(timer):
    assert timer.phase is Phase.IDLE
    assert timer.is_running is False
    assert timer.completed_focus_count == 0
    # Em IDLE, remaining_seconds é a duração do foco.
    assert timer.remaining_seconds == 60.0


def test_start_from_idle_begins_focus(timer):
    timer.start()
    assert timer.phase is Phase.FOCUS
    assert timer.is_running is True
    assert timer.remaining_seconds == 60.0


def test_start_while_running_does_not_restart_block(timer, clock):
    timer.start()
    clock.advance(20)
    timer.start()
    assert timer.phase is Phase.FOCUS
    assert timer.remaining_seconds == pytest.approx(40.0)


def test_remaining_seconds_is_live_without_tick(timer, clock):
    timer.start()
    clock.advance(15)
    assert timer.remaining_seconds == pytest.approx(45.0)


# ---- pause / start -----------------------------------------------------


def test_pause_freezes_and_resume_preserves_remaining(timer, clock):
    timer.start()
    clock.advance(20)
    timer.pause()
    assert timer.is_running is False
    assert timer.remaining_seconds == pytest.approx(40.0)

    clock.advance(1000)  # tempo pausado não deve contar
    assert timer.remaining_seconds == pytest.approx(40.0)
    assert timer.tick() is None

    timer.start()
    clock.advance(10)
    assert timer.remaining_seconds == pytest.approx(30.0)
    assert timer.phase is Phase.FOCUS


def test_pause_when_idle_is_noop(timer):
    timer.pause()
    assert timer.phase is Phase.IDLE
    assert timer.is_running is False
    assert timer.remaining_seconds == 60.0


def test_pause_twice_is_noop(timer, clock):
    timer.start()
    clock.advance(10)
    timer.pause()
    timer.pause()
    assert timer.remaining_seconds == pytest.approx(50.0)
    assert timer.is_running is False


# ---- tick --------------------------------------------------------------


def test_tick_without_transition_returns_none(timer, clock):
    timer.start()
    clock.advance(30)
    assert timer.tick() is None
    assert timer.phase is Phase.FOCUS
    assert timer.remaining_seconds == pytest.approx(30.0)


def test_tick_when_not_running_returns_none(timer, clock):
    assert timer.tick() is None
    timer.start()
    clock.advance(10)
    timer.pause()
    clock.advance(500)
    assert timer.tick() is None
    assert timer.phase is Phase.FOCUS


def test_tick_returns_transition_event_when_focus_ends(timer, clock):
    timer.start()
    clock.advance(60)
    event = timer.tick()
    assert event == TransitionEvent(finished=Phase.FOCUS, next=Phase.SHORT_BREAK)
    assert timer.phase is Phase.SHORT_BREAK
    assert timer.is_running is True
    assert timer.completed_focus_count == 1


def test_tick_processes_only_one_transition_per_call(timer, clock):
    timer.start()
    clock.advance(200)  # passou de mais de um bloco
    event = timer.tick()
    assert event == TransitionEvent(finished=Phase.FOCUS, next=Phase.SHORT_BREAK)
    # Excedente descartado: o novo bloco começa com duração cheia agora.
    assert timer.phase is Phase.SHORT_BREAK
    assert timer.remaining_seconds == pytest.approx(60.0)
    assert timer.tick() is None


# ---- fluxo completo ----------------------------------------------------


def test_full_flow_focus_short_break_focus(timer, clock, no_sleep):
    timer.start()
    clock.advance(60)
    assert timer.tick() == TransitionEvent(Phase.FOCUS, Phase.SHORT_BREAK)

    clock.advance(60)
    assert timer.tick() == TransitionEvent(Phase.SHORT_BREAK, Phase.FOCUS)
    assert timer.phase is Phase.FOCUS
    assert timer.completed_focus_count == 1
    assert timer.remaining_seconds == pytest.approx(60.0)


def test_long_break_after_n_focus_then_counter_resets(timer, clock, no_sleep):
    timer.start()  # cycles_before_long_break = 2

    clock.advance(60)  # foco 1 concluído
    assert timer.tick() == TransitionEvent(Phase.FOCUS, Phase.SHORT_BREAK)
    clock.advance(60)
    assert timer.tick() == TransitionEvent(Phase.SHORT_BREAK, Phase.FOCUS)

    clock.advance(60)  # foco 2 concluído -> pausa longa
    assert timer.tick() == TransitionEvent(Phase.FOCUS, Phase.LONG_BREAK)
    assert timer.completed_focus_count == 2
    assert timer.remaining_seconds == pytest.approx(120.0)

    clock.advance(120)  # pausa longa concluída -> zera contador
    assert timer.tick() == TransitionEvent(Phase.LONG_BREAK, Phase.FOCUS)
    assert timer.completed_focus_count == 0

    clock.advance(60)  # próximo foco concluído -> volta a pausa curta
    assert timer.tick() == TransitionEvent(Phase.FOCUS, Phase.SHORT_BREAK)
    assert timer.completed_focus_count == 1


# ---- skip --------------------------------------------------------------


def test_skip_focus_goes_to_break_without_incrementing(timer, clock):
    timer.start()
    clock.advance(10)
    timer.skip()
    assert timer.phase is Phase.SHORT_BREAK
    assert timer.completed_focus_count == 0
    assert timer.remaining_seconds == pytest.approx(60.0)


def test_skip_focus_at_threshold_minus_one_gives_short_break(timer, clock, no_sleep):
    timer.start()
    clock.advance(60)
    timer.tick()  # foco 1 concluído (count = 1, threshold = 2)
    clock.advance(60)
    timer.tick()  # pausa curta concluída -> foco
    timer.skip()  # pula foco 2: não incrementa, pausa curta (count ainda 1)
    assert timer.phase is Phase.SHORT_BREAK
    assert timer.completed_focus_count == 1


def test_skip_short_break_goes_to_focus(timer, clock):
    timer.start()
    clock.advance(60)
    timer.tick()  # entra em pausa curta
    timer.skip()
    assert timer.phase is Phase.FOCUS
    assert timer.completed_focus_count == 1
    assert timer.remaining_seconds == pytest.approx(60.0)


def test_skip_long_break_goes_to_focus_and_resets_counter(timer, clock, no_sleep):
    timer.start()
    clock.advance(60)
    timer.tick()
    clock.advance(60)
    timer.tick()
    clock.advance(60)
    timer.tick()  # entra em pausa longa, count = 2
    assert timer.phase is Phase.LONG_BREAK

    timer.skip()
    assert timer.phase is Phase.FOCUS
    assert timer.completed_focus_count == 0


def test_skip_keeps_paused_state(timer, clock):
    timer.start()
    clock.advance(10)
    timer.pause()
    timer.skip()
    assert timer.phase is Phase.SHORT_BREAK
    assert timer.is_running is False
    assert timer.remaining_seconds == pytest.approx(60.0)


def test_skip_when_idle_is_noop(timer):
    timer.skip()
    assert timer.phase is Phase.IDLE
    assert timer.is_running is False
    assert timer.completed_focus_count == 0


# ---- reset -------------------------------------------------------------


def test_reset_returns_to_idle_and_clears_counter(timer, clock, no_sleep):
    timer.start()
    clock.advance(60)
    timer.tick()
    assert timer.completed_focus_count == 1

    timer.reset()
    assert timer.phase is Phase.IDLE
    assert timer.is_running is False
    assert timer.completed_focus_count == 0
    assert timer.remaining_seconds == 60.0
    assert timer.tick() is None
