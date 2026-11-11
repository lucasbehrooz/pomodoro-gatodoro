"""Períodos do seletor (7 dias, 30 dias, mês atual) e rótulos do gráfico."""

import os
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from pomodoro.storage import Storage
from pomodoro.timer import Phase
from pomodoro.ui.stats import (
    PERIOD_LABELS,
    build_period_series,
    label_step,
    period_range,
    period_total,
)

TODAY = date(2026, 11, 10)


def at(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, 10, 0, 0)


@pytest.fixture
def storage(tmp_path: Path):
    s = Storage(tmp_path / "pomodoro.db")
    yield s
    s.close()


def focus(storage: Storage, day: date, n: int = 1) -> None:
    for _ in range(n):
        storage.record_session(Phase.FOCUS, at(day), 1500, True)


def test_period_range_last_7_and_30():
    assert period_range("7", TODAY) == (TODAY - timedelta(days=6), TODAY)
    assert period_range("30", TODAY) == (TODAY - timedelta(days=29), TODAY)


def test_period_range_current_month():
    assert period_range("month", TODAY) == (date(2026, 11, 1), TODAY)
    # No dia 1, o mês atual tem só um dia.
    assert period_range("month", date(2026, 12, 1)) == (date(2026, 12, 1), date(2026, 12, 1))


def test_period_range_unknown_raises():
    with pytest.raises(ValueError):
        period_range("ano", TODAY)


def test_series_30_days_has_30_items_with_zeros(storage):
    focus(storage, TODAY - timedelta(days=20), 3)
    series = build_period_series(storage, TODAY, "30")
    assert len(series) == 30
    assert series[0][0] == TODAY - timedelta(days=29)
    assert series[-1][0] == TODAY
    assert dict(series)[TODAY - timedelta(days=20)] == 3
    assert sum(c for _, c in series) == 3


def test_period_total_month_excludes_previous_month(storage):
    focus(storage, date(2026, 10, 31), 4)  # mês anterior
    focus(storage, date(2026, 11, 2), 2)
    focus(storage, TODAY, 1)
    assert period_total(storage, TODAY, "month") == 3
    assert period_total(storage, TODAY, "30") == 7


def test_period_total_ignores_breaks(storage):
    storage.record_session(Phase.SHORT_BREAK, at(TODAY), 300, True)
    focus(storage, TODAY, 1)
    assert period_total(storage, TODAY, "7") == 1


def test_label_step_keeps_labels_few():
    assert label_step(7) == 1
    assert label_step(30) == 5
    assert label_step(31) == 5
    assert label_step(1) == 1


def test_period_labels_map_to_known_keys():
    assert set(PERIOD_LABELS.values()) == {"7", "30", "month"}


def test_window_switches_period():
    if os.environ.get("POMODORO_UI_SMOKE") != "1":
        pytest.skip("smoke de janela: defina POMODORO_UI_SMOKE=1")
    import customtkinter as ctk

    from pomodoro.ui.stats import StatsWindow

    tmp = Path(os.environ.get("TMPDIR", "/tmp")) / "pomodoro-smoke-periods.db"
    if tmp.exists():
        tmp.unlink()
    s = Storage(tmp)
    try:
        root = ctk.CTk()
        win = StatsWindow(root, s, today=lambda: TODAY)
        win._on_period_selected("30 dias")
        assert win._period_key == "30"
        win._on_period_selected("Mês atual")
        assert win._period_key == "month"
        win.destroy()
        root.destroy()
    finally:
        s.close()
