import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from pomodoro.storage import Storage
from pomodoro.timer import Phase

D1 = date(2026, 11, 9)
D2 = date(2026, 11, 10)
D3 = date(2026, 11, 11)


def at(day: date, hour: int = 10) -> datetime:
    return datetime(day.year, day.month, day.day, hour, 0, 0)


@pytest.fixture
def storage(tmp_path: Path):
    s = Storage(tmp_path / "pomodoro.db")
    yield s
    s.close()


def test_creates_parent_dir_and_db_file(tmp_path: Path):
    db = tmp_path / "sub" / "dir" / "p.db"
    with Storage(db):
        pass
    assert db.exists()


def test_count_completed_focus_by_day(storage: Storage):
    storage.record_session(Phase.FOCUS, at(D2, 9), 1500, True)
    storage.record_session(Phase.FOCUS, at(D2, 14), 1500, True)
    storage.record_session(Phase.FOCUS, at(D1, 9), 1500, True)

    assert storage.count_completed_focus(D2) == 2
    assert storage.count_completed_focus(D1) == 1
    assert storage.count_completed_focus(D3) == 0


def test_count_between_is_inclusive(storage: Storage):
    storage.record_session(Phase.FOCUS, at(D1), 1500, True)
    storage.record_session(Phase.FOCUS, at(D2), 1500, True)
    storage.record_session(Phase.FOCUS, at(D3), 1500, True)

    assert storage.count_completed_focus_between(D1, D2) == 2
    assert storage.count_completed_focus_between(D1, D3) == 3
    assert storage.count_completed_focus_between(D2, D2) == 1


def test_incomplete_sessions_and_breaks_do_not_count(storage: Storage):
    storage.record_session(Phase.FOCUS, at(D2, 9), 600, False)
    storage.record_session(Phase.SHORT_BREAK, at(D2, 10), 300, True)
    storage.record_session(Phase.LONG_BREAK, at(D2, 11), 900, True)
    storage.record_session(Phase.FOCUS, at(D2, 12), 1500, True)

    assert storage.count_completed_focus(D2) == 1


def test_idle_phase_is_rejected(storage: Storage):
    with pytest.raises(ValueError):
        storage.record_session(Phase.IDLE, at(D2), 0, True)


def test_daily_counts_fill_zeros(storage: Storage):
    storage.record_session(Phase.FOCUS, at(D1), 1500, True)
    storage.record_session(Phase.FOCUS, at(D1, 15), 1500, True)
    storage.record_session(Phase.FOCUS, at(D3), 1500, False)  # não conta

    counts = storage.daily_focus_counts(D1, D3)

    assert counts == {D1: 2, D2: 0, D3: 0}


def test_daily_counts_single_day_range(storage: Storage):
    assert storage.daily_focus_counts(D2, D2) == {D2: 0}


def test_invalid_range_raises(storage: Storage):
    with pytest.raises(ValueError):
        storage.count_completed_focus_between(D3, D1)
    with pytest.raises(ValueError):
        storage.daily_focus_counts(D3, D1)


def test_data_persists_across_instances(tmp_path: Path):
    db = tmp_path / "p.db"
    first = Storage(db)
    first.record_session(Phase.FOCUS, at(D2), 1500, True)
    first.close()

    second = Storage(db)
    try:
        assert second.count_completed_focus(D2) == 1
    finally:
        second.close()


def test_close_is_idempotent_and_context_manager_closes(tmp_path: Path):
    db = tmp_path / "p.db"
    with Storage(db) as s:
        s.record_session(Phase.FOCUS, at(D2), 1500, True)
    s.close()  # não deve falhar

    with pytest.raises(sqlite3.ProgrammingError):
        s.count_completed_focus(D2)


def test_today_and_week_counts(storage: Storage):
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    storage.record_session(Phase.FOCUS, at(today), 1500, True)
    storage.record_session(Phase.FOCUS, at(monday), 1500, True)
    # fora da semana corrente
    storage.record_session(Phase.FOCUS, at(monday - timedelta(days=1)), 1500, True)

    # Se hoje é segunda, os dois registros caem no mesmo dia.
    assert storage.today_count() == (2 if today == monday else 1)
    assert storage.week_count() == 2
