"""Sequência de dias com foco concluído (F04): consulta no storage e funções puras."""

from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from pomodoro.storage import Storage
from pomodoro.timer import Phase
from pomodoro.ui.stats import format_days, record_streak, streak, streak_line

TODAY = date(2026, 11, 10)


def d(offset: int) -> date:
    """Dia relativo a TODAY (0 = hoje, -1 = ontem...)."""
    return TODAY + timedelta(days=offset)


@pytest.fixture
def storage(tmp_path: Path):
    s = Storage(tmp_path / "pomodoro.db")
    yield s
    s.close()


# ---- streak -----------------------------------------------------------------


def test_streak_vazio():
    assert streak([], TODAY) == 0


def test_streak_hoje_com_foco_conta_hoje():
    assert streak([d(-2), d(-1), d(0)], TODAY) == 3


def test_streak_hoje_sem_foco_termina_ontem():
    assert streak([d(-3), d(-2), d(-1)], TODAY) == 3


def test_streak_sem_foco_hoje_nem_ontem_zera():
    assert streak([d(-4), d(-3), d(-2)], TODAY) == 0


def test_streak_para_no_buraco():
    assert streak([d(-6), d(-5), d(-4), d(-2), d(-1), d(0)], TODAY) == 3


def test_streak_so_hoje():
    assert streak([d(0)], TODAY) == 1


def test_streak_ignora_dias_futuros_e_duplicados():
    assert streak([d(-1), d(-1), d(0), d(1), d(2)], TODAY) == 2


def test_streak_atravessa_virada_de_mes():
    days = [date(2026, 10, 30), date(2026, 10, 31), date(2026, 11, 1)]
    assert streak(days, date(2026, 11, 1)) == 3


# ---- record_streak ----------------------------------------------------------


def test_recorde_vazio():
    assert record_streak([]) == 0


def test_recorde_maior_que_sequencia_atual():
    days = [d(-20), d(-19), d(-18), d(-17), d(-16), d(-2), d(-1), d(0)]
    assert streak(days, TODAY) == 3
    assert record_streak(days) == 5


def test_recorde_igual_a_sequencia_atual():
    assert record_streak([d(-10), d(-2), d(-1), d(0)]) == 3


def test_recorde_fora_de_ordem_e_duplicado():
    assert record_streak([d(0), d(-2), d(-1), d(-1), d(-5)]) == 3


# ---- texto ------------------------------------------------------------------


def test_format_days_singular_e_plural():
    assert format_days(0) == "0 dias"
    assert format_days(1) == "1 dia"
    assert format_days(5) == "5 dias"


def test_streak_line():
    assert streak_line(5, 12) == "Sequência: 5 dias · Recorde: 12 dias"
    assert streak_line(1, 1) == "Sequência: 1 dia · Recorde: 1 dia"


# ---- storage.completed_focus_days ------------------------------------------


def at(day: date, hour: int = 10) -> datetime:
    return datetime(day.year, day.month, day.day, hour)


def test_completed_focus_days_banco_vazio(storage: Storage):
    assert storage.completed_focus_days() == []
    assert streak(storage.completed_focus_days(), TODAY) == 0
    assert record_streak(storage.completed_focus_days()) == 0


def test_completed_focus_days_distintos_e_ordenados(storage: Storage):
    storage.record_session(Phase.FOCUS, at(d(0), 9), 1500, True)
    storage.record_session(Phase.FOCUS, at(d(-2)), 1500, True)
    storage.record_session(Phase.FOCUS, at(d(0), 15), 1500, True)
    assert storage.completed_focus_days() == [d(-2), d(0)]


def test_focos_interrompidos_e_pausas_nao_contam(storage: Storage):
    storage.record_session(Phase.FOCUS, at(d(-2)), 1500, True)
    storage.record_session(Phase.FOCUS, at(d(-1)), 600, False)  # interrompido
    storage.record_session(Phase.SHORT_BREAK, at(d(-1), 11), 300, True)  # pausa
    storage.record_session(Phase.LONG_BREAK, at(d(0)), 900, True)  # pausa
    days = storage.completed_focus_days()
    assert days == [d(-2)]
    assert streak(days, TODAY) == 0
    assert record_streak(days) == 1


def test_completed_focus_days_usa_dia_local(storage: Storage):
    from datetime import timezone

    # Data aware é gravada em horário local; o dia da consulta é o local.
    aware = datetime(2026, 11, 10, 12, tzinfo=timezone.utc)
    storage.record_session(Phase.FOCUS, aware, 1500, True)
    assert storage.completed_focus_days() == [aware.astimezone().date()]
