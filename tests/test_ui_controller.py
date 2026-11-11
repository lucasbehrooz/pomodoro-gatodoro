import sqlite3
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from pomodoro.config import Config
from pomodoro.notifier import NullNotifier
from pomodoro.storage import Storage
from pomodoro.timer import Phase
from pomodoro.ui.controller import (
    ALERT_PAUSE_SECONDS,
    NOISE_FADE_SECONDS,
    ApplyStatus,
    PomodoroController,
    format_mmss,
)

BASE = datetime(2026, 11, 10, 10, 0, 0)
DAY = date(2026, 11, 10)


class FakeClock:
    def __init__(self) -> None:
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


class FakeNotifier:
    def __init__(self) -> None:
        self.alerts = 0
        self.toasts: list[tuple[str, str]] = []

    def alert_sound(self) -> None:
        self.alerts += 1

    def toast(self, title: str, message: str) -> None:
        self.toasts.append((title, message))


class FakeNoise:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def start(self, fade_seconds: float) -> None:
        self.calls.append(("start", fade_seconds))

    def stop(self, fade_seconds: float) -> None:
        self.calls.append(("stop", fade_seconds))

    def set_volume(self, volume: float) -> None:
        self.calls.append(("set_volume", volume))

    def pause_for_alert(self, seconds: float) -> None:
        self.calls.append(("pause_for_alert", seconds))

    def names(self) -> list[str]:
        return [c[0] for c in self.calls]


class BrokenStorage:
    def record_session(self, *args, **kwargs) -> None:
        raise sqlite3.OperationalError("disco cheio")


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def storage(tmp_path: Path):
    s = Storage(tmp_path / "pomodoro.db")
    yield s
    s.close()


@pytest.fixture
def cfg() -> Config:
    # foco 60 s, pausa curta 60 s, pausa longa 120 s, pausa longa após 2 focos
    return Config(
        focus_minutes=1,
        short_break_minutes=1,
        long_break_minutes=2,
        cycles_before_long_break=2,
        sound_enabled=True,
        toast_enabled=True,
        brown_noise_enabled=False,
        brown_noise_focus_only=True,
        brown_noise_volume=0.3,
    )


@pytest.fixture
def notifier() -> FakeNotifier:
    return FakeNotifier()


def make(cfg, storage, clock, notifier=None, noise=None, notifier_factory=None):
    return PomodoroController(
        cfg,
        storage,
        notifier=notifier or FakeNotifier(),
        noise_player=noise,
        notifier_factory=notifier_factory,
        clock=clock,
        now=lambda: BASE + timedelta(seconds=clock.t - 1000.0),
    )


def rows(storage: Storage) -> list[tuple[str, int, int, str]]:
    con = sqlite3.connect(storage.path)
    try:
        return con.execute(
            "SELECT phase, duration_seconds, completed, started_at FROM sessions ORDER BY id"
        ).fetchall()
    finally:
        con.close()


# ---- formatação -------------------------------------------------------


@pytest.mark.parametrize(
    "seconds, expected",
    [(1500, "25:00"), (59.2, "01:00"), (0, "00:00"), (-3, "00:00"), (61, "01:01")],
)
def test_format_mmss(seconds, expected):
    assert format_mmss(seconds) == expected


# ---- fluxo start / pause / skip / reset -------------------------------


def test_initial_state_is_idle(cfg, storage, clock):
    c = make(cfg, storage, clock)
    assert c.phase is Phase.IDLE
    assert c.phase_label == "Ocioso"
    assert not c.is_running
    assert c.remaining_seconds == 60


def test_start_begins_focus(cfg, storage, clock):
    c = make(cfg, storage, clock)
    c.start()
    assert c.phase is Phase.FOCUS
    assert c.phase_label == "Foco"
    assert c.is_running


def test_pause_keeps_remaining_and_resume_continues(cfg, storage, clock):
    c = make(cfg, storage, clock)
    c.start()
    clock.advance(20)
    c.pause()
    assert c.remaining_seconds == pytest.approx(40)
    clock.advance(100)
    assert c.remaining_seconds == pytest.approx(40)
    c.start()
    clock.advance(10)
    assert c.remaining_seconds == pytest.approx(30)


def test_toggle_alternates(cfg, storage, clock):
    c = make(cfg, storage, clock)
    c.toggle()
    assert c.is_running
    c.toggle()
    assert not c.is_running


def test_skip_idle_is_noop(cfg, storage, clock):
    c = make(cfg, storage, clock)
    c.skip()
    assert c.phase is Phase.IDLE
    assert rows(storage) == []


def test_reset_records_interrupted_focus_and_returns_to_idle(cfg, storage, clock):
    c = make(cfg, storage, clock)
    c.start()
    clock.advance(15)
    c.reset()
    assert c.phase is Phase.IDLE
    assert c.remaining_seconds == 60
    assert rows(storage) == [("focus", 15, 0, BASE.isoformat())]


def test_reset_idle_records_nothing(cfg, storage, clock):
    c = make(cfg, storage, clock)
    c.reset()
    assert rows(storage) == []


def test_skip_focus_records_interrupted_and_next_block_counts(cfg, storage, clock):
    c = make(cfg, storage, clock)
    c.start()
    clock.advance(30)
    c.skip()
    assert c.phase is Phase.SHORT_BREAK
    assert c.is_running
    assert c.completed_focus_count == 0  # pular foco não conta
    assert rows(storage) == [("focus", 30, 0, BASE.isoformat())]


def test_skip_paused_then_resume_uses_resume_time_as_start(cfg, storage, clock):
    c = make(cfg, storage, clock)
    c.start()
    clock.advance(10)
    c.pause()
    c.skip()  # foco de 10 s interrompido; pausa curta começa pausada
    assert c.phase is Phase.SHORT_BREAK
    assert not c.is_running
    assert c.remaining_seconds == 60

    clock.advance(50)  # pausado, nada conta
    c.start()
    clock.advance(12)
    c.reset()
    assert rows(storage) == [
        ("focus", 10, 0, BASE.isoformat()),
        ("short_break", 12, 0, (BASE + timedelta(seconds=60)).isoformat()),
    ]


def test_reset_clears_cycle_count(cfg, storage, clock):
    c = make(cfg, storage, clock)
    c.start()
    clock.advance(60)
    c.tick()
    assert c.completed_focus_count == 1
    c.reset()
    assert c.completed_focus_count == 0


# ---- transições e registro --------------------------------------------


def test_tick_transition_records_completed_and_notifies(cfg, storage, clock, notifier):
    c = make(cfg, storage, clock, notifier=notifier)
    c.start()
    clock.advance(59)
    assert c.tick() is None
    clock.advance(1)
    event = c.tick()
    assert event is not None
    assert event.finished is Phase.FOCUS
    assert event.next is Phase.SHORT_BREAK
    assert c.completed_focus_count == 1
    assert rows(storage) == [("focus", 60, 1, BASE.isoformat())]
    assert storage.count_completed_focus(DAY) == 1
    assert notifier.alerts == 1
    assert notifier.toasts == [("Pomodoro Gatodoro", "Hora da pausa")]


def test_tick_break_completion_records_break_and_announces_focus(cfg, storage, clock, notifier):
    c = make(cfg, storage, clock, notifier=notifier)
    c.start()
    clock.advance(60)
    c.tick()  # foco -> pausa curta
    clock.advance(60)
    event = c.tick()  # pausa curta -> foco
    assert event.finished is Phase.SHORT_BREAK
    assert event.next is Phase.FOCUS
    assert c.phase is Phase.FOCUS
    assert notifier.toasts[-1] == ("Pomodoro Gatodoro", "Hora de focar")
    recorded = rows(storage)
    assert recorded[1][:3] == ("short_break", 60, 1)
    # a pausa começou no tick da transição foco -> pausa (BASE + 60 s)
    assert recorded[1][3] == (BASE + timedelta(seconds=60)).isoformat()
    assert c.is_running


def test_long_break_after_configured_cycles(cfg, storage, clock):
    c = make(cfg, storage, clock)
    c.start()
    clock.advance(60)
    c.tick()  # foco 1 -> pausa curta
    assert c.phase is Phase.SHORT_BREAK
    clock.advance(60)
    c.tick()  # pausa curta -> foco 2
    assert c.phase is Phase.FOCUS
    clock.advance(60)
    c.tick()  # foco 2 concluído (2 == cycles_before_long_break) -> pausa longa
    assert c.phase is Phase.LONG_BREAK
    assert c.remaining_seconds == 120
    assert c.completed_focus_count == 2


def test_tick_while_paused_returns_none(cfg, storage, clock):
    c = make(cfg, storage, clock)
    c.start()
    clock.advance(10)
    c.pause()
    clock.advance(1000)
    assert c.tick() is None
    assert rows(storage) == []


def test_shutdown_records_running_block_as_interrupted(cfg, storage, clock):
    c = make(cfg, storage, clock)
    c.start()
    clock.advance(25)
    c.shutdown()
    assert rows(storage) == [("focus", 25, 0, BASE.isoformat())]


def test_storage_failure_does_not_break_timer(cfg, clock):
    c = make(cfg, BrokenStorage(), clock, notifier=NullNotifier())
    c.start()
    clock.advance(60)
    event = c.tick()
    assert event is not None
    assert c.phase is Phase.SHORT_BREAK


# ---- aplicação de configuração ----------------------------------------


def test_apply_config_idle_recreates_timer(cfg, storage, clock):
    c = make(cfg, storage, clock)
    status = c.apply_config(replace(cfg, focus_minutes=2))
    assert status is ApplyStatus.APPLIED
    assert not c.timer_config_pending
    c.start()
    assert c.remaining_seconds == 120


def test_apply_timer_fields_while_running_is_deferred_until_reset(cfg, storage, clock):
    c = make(cfg, storage, clock)
    c.start()
    clock.advance(10)
    status = c.apply_config(replace(cfg, focus_minutes=2))
    assert status is ApplyStatus.DEFERRED
    assert c.timer_config_pending
    assert c.remaining_seconds == pytest.approx(50)  # bloco atual intacto
    assert c.config.focus_minutes == 2

    c.reset()
    assert not c.timer_config_pending
    c.start()
    assert c.remaining_seconds == 120


def test_deferred_config_reverted_clears_pending(cfg, storage, clock):
    c = make(cfg, storage, clock)
    c.start()
    c.apply_config(replace(cfg, cycles_before_long_break=3))
    assert c.timer_config_pending
    status = c.apply_config(cfg)
    assert status is ApplyStatus.APPLIED
    assert not c.timer_config_pending


def test_non_timer_fields_apply_immediately_while_running(cfg, storage, clock):
    old = FakeNotifier()
    new = FakeNotifier()
    created = []

    def factory(config):
        created.append(config)
        return new

    c = make(cfg, storage, clock, notifier=old, notifier_factory=factory)
    c.start()
    status = c.apply_config(replace(cfg, sound_enabled=False, toast_enabled=True))
    assert status is ApplyStatus.APPLIED
    assert created[-1].sound_enabled is False
    clock.advance(60)
    c.tick()
    assert old.alerts == 0 and old.toasts == []
    assert new.alerts == 0  # som desligado no config novo
    assert new.toasts == [("Pomodoro Gatodoro", "Hora da pausa")]


# ---- ruído ------------------------------------------------------------


def noise_cfg(cfg, **kw):
    return replace(cfg, brown_noise_enabled=True, **kw)


def test_noise_disabled_never_starts(cfg, storage, clock):
    noise = FakeNoise()
    c = make(cfg, storage, clock, noise=noise)
    c.start()
    clock.advance(60)
    c.tick()
    assert noise.calls == []


def test_noise_starts_on_focus_and_stops_on_pause(storage, clock, cfg):
    noise = FakeNoise()
    c = make(noise_cfg(cfg, brown_noise_volume=0.5), storage, clock, noise=noise)
    c.start()
    assert noise.calls == [("set_volume", 0.5), ("start", NOISE_FADE_SECONDS)]
    assert c.noise_playing
    c.pause()
    assert noise.calls[-1] == ("stop", NOISE_FADE_SECONDS)
    assert not c.noise_playing


def test_noise_focus_only_stops_on_break(storage, clock, cfg):
    noise = FakeNoise()
    c = make(noise_cfg(cfg, brown_noise_focus_only=True), storage, clock, noise=noise)
    c.start()
    clock.advance(60)
    c.tick()  # entra na pausa curta: ruído para antes do alerta
    assert c.phase is Phase.SHORT_BREAK
    assert noise.names() == ["set_volume", "start", "stop"]
    assert not c.noise_playing


def test_noise_focus_only_stops_on_skip_into_break(storage, clock, cfg):
    noise = FakeNoise()
    c = make(noise_cfg(cfg), storage, clock, noise=noise)
    c.start()
    c.skip()
    assert c.phase is Phase.SHORT_BREAK
    assert noise.names() == ["set_volume", "start", "stop"]
    assert not c.noise_playing


def test_noise_plays_in_breaks_when_not_focus_only(storage, clock, cfg):
    noise = FakeNoise()
    c = make(noise_cfg(cfg, brown_noise_focus_only=False), storage, clock, noise=noise)
    c.start()
    clock.advance(60)
    c.tick()  # pausa curta: continua tocando
    assert c.phase is Phase.SHORT_BREAK
    assert c.noise_playing
    assert noise.names().count("start") == 1
    assert "stop" not in noise.names()


def test_alert_pauses_noise_when_playing(storage, clock, cfg):
    noise = FakeNoise()
    c = make(noise_cfg(cfg, brown_noise_focus_only=False), storage, clock, noise=noise)
    c.start()
    clock.advance(60)
    c.tick()
    assert ("pause_for_alert", ALERT_PAUSE_SECONDS) in noise.calls


def test_alert_does_not_pause_noise_when_sound_disabled(storage, clock, cfg):
    noise = FakeNoise()
    c = make(
        noise_cfg(cfg, brown_noise_focus_only=False, sound_enabled=False),
        storage,
        clock,
        noise=noise,
    )
    c.start()
    clock.advance(60)
    c.tick()
    assert "pause_for_alert" not in noise.names()


def test_noise_volume_change_while_playing(storage, clock, cfg):
    noise = FakeNoise()
    c = make(noise_cfg(cfg), storage, clock, noise=noise)
    c.start()
    c.apply_config(noise_cfg(cfg, brown_noise_volume=0.8))
    assert ("set_volume", 0.8) in noise.calls
    assert c.noise_playing


def test_disabling_noise_while_playing_stops_it(storage, clock, cfg):
    noise = FakeNoise()
    c = make(noise_cfg(cfg), storage, clock, noise=noise)
    c.start()
    c.apply_config(cfg)  # brown_noise_enabled volta a False
    assert noise.calls[-1] == ("stop", NOISE_FADE_SECONDS)
    assert not c.noise_playing


def test_missing_noise_player_is_tolerated(storage, clock, cfg):
    c = make(noise_cfg(cfg), storage, clock, noise=None)
    c.start()
    clock.advance(60)
    assert c.tick() is not None
    c.shutdown()
    assert not c.noise_playing


def test_shutdown_stops_noise(storage, clock, cfg):
    noise = FakeNoise()
    c = make(noise_cfg(cfg), storage, clock, noise=noise)
    c.start()
    c.shutdown()
    assert noise.calls[-1] == ("stop", NOISE_FADE_SECONDS)
