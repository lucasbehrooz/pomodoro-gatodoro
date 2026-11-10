"""Testes da tela de estatísticas.

As funções puras (build_week_series, summarize, bar_geometry) não usam Tk.
O smoke da janela abre uma janela real e só roda com opt-in:

    POMODORO_UI_SMOKE=1 pytest tests/test_stats.py
"""

import os
from datetime import date, datetime
from pathlib import Path

import pytest

from pomodoro.storage import Storage
from pomodoro.timer import Phase
from pomodoro.ui.stats import bar_geometry, build_week_series, summarize

# 2026-11-10 é terça-feira. A semana corrente é seg 09/11 a dom 15/11.
TODAY = date(2026, 11, 10)
MON = date(2026, 11, 9)


def at(day: date, hour: int = 10) -> datetime:
    return datetime(day.year, day.month, day.day, hour, 0, 0)


@pytest.fixture
def storage(tmp_path: Path):
    s = Storage(tmp_path / "pomodoro.db")
    yield s
    s.close()


def seed(storage: Storage) -> None:
    """Dados de exemplo (focos concluídos, salvo indicação contrária)."""
    storage.record_session(Phase.FOCUS, at(date(2026, 11, 3)), 1500, True)  # fora dos 7 dias
    storage.record_session(Phase.FOCUS, at(date(2026, 11, 5)), 1500, True)
    storage.record_session(Phase.FOCUS, at(date(2026, 11, 5), 14), 1500, True)
    storage.record_session(Phase.FOCUS, at(date(2026, 11, 5), 16), 1500, True)
    storage.record_session(Phase.FOCUS, at(date(2026, 11, 8)), 1500, True)  # domingo anterior
    storage.record_session(Phase.FOCUS, at(MON), 1500, True)
    storage.record_session(Phase.FOCUS, at(TODAY, 9), 1500, True)
    storage.record_session(Phase.FOCUS, at(TODAY, 11), 1500, True)
    storage.record_session(Phase.FOCUS, at(TODAY, 15), 600, False)  # interrompido
    storage.record_session(Phase.SHORT_BREAK, at(TODAY, 16), 300, True)  # pausa


# ---- build_week_series -------------------------------------------------------


def test_week_series_has_seven_items_in_order_with_zeros(storage: Storage):
    seed(storage)

    series = build_week_series(storage, TODAY)

    assert len(series) == 7
    days = [day for day, _ in series]
    assert days == sorted(days)
    assert days[0] == date(2026, 11, 4)
    assert days[-1] == TODAY
    assert series == [
        (date(2026, 11, 4), 0),
        (date(2026, 11, 5), 3),
        (date(2026, 11, 6), 0),
        (date(2026, 11, 7), 0),
        (date(2026, 11, 8), 1),  # domingo anterior, dentro da janela de 7 dias
        (date(2026, 11, 9), 1),
        (date(2026, 11, 10), 2),
    ]


def test_week_series_empty_database_is_all_zeros(storage: Storage):
    series = build_week_series(storage, TODAY)

    assert len(series) == 7
    assert all(count == 0 for _, count in series)


def test_week_series_custom_length(storage: Storage):
    seed(storage)

    series = build_week_series(storage, TODAY, days=3)

    assert [day for day, _ in series] == [date(2026, 11, 8), date(2026, 11, 9), TODAY]
    assert [count for _, count in series] == [1, 1, 2]  # 08 tem 1 foco na seed


def test_week_series_rejects_non_positive_days(storage: Storage):
    with pytest.raises(ValueError):
        build_week_series(storage, TODAY, days=0)


# ---- summarize ---------------------------------------------------------------


def test_summarize_today_week_and_last_7_days(storage: Storage):
    seed(storage)

    totals = summarize(storage, TODAY)

    assert totals == {
        "today": 2,  # incompleto e pausa não contam
        "week": 3,  # seg 09 (1) + ter 10 (2); domingo 08 é da semana anterior
        # 04..10: 05 (3) + 08 (1) + 09 (1) + 10 (2); o dia 03 fica de fora
        "last_7_days": 7,
    }


def test_summarize_week_excludes_previous_sunday_but_last_7_includes_it(storage: Storage):
    seed(storage)

    totals = summarize(storage, TODAY)

    assert totals["week"] == 3  # sem o domingo 08
    assert totals["last_7_days"] == 7  # com o domingo 08


def test_summarize_week_is_monday_to_sunday_when_today_is_sunday(storage: Storage):
    seed(storage)
    sunday = date(2026, 11, 15)

    totals = summarize(storage, sunday)

    assert totals["today"] == 0
    assert totals["week"] == 3  # seg 09 até dom 15 cobre os focos de 09 e 10
    # 09..15: 09 (1) + 10 (2); o domingo 08 fica fora da janela
    assert totals["last_7_days"] == 3


def test_summarize_empty_database(storage: Storage):
    assert summarize(storage, TODAY) == {"today": 0, "week": 0, "last_7_days": 0}


# ---- bar_geometry ------------------------------------------------------------


def heights(rects: list[tuple[int, int, int, int]]) -> list[int]:
    return [y1 - y0 for _, y0, _, y1 in rects]


def test_bar_heights_are_proportional_to_max():
    # área interna: 110 - 2*10 = 90 px; máximo 10 -> altura máxima 90
    rects = bar_geometry([0, 5, 10], width=100, height=110, padding=10)

    assert heights(rects) == [0, 45, 90]


def test_bars_share_baseline_and_do_not_overlap():
    rects = bar_geometry([2, 4, 1, 3], width=200, height=120, padding=10)

    assert all(y1 == 110 for _, _, _, y1 in rects)  # linha de base = height - padding
    for (_, _, x1, _), (nx0, _, _, _) in zip(rects, rects[1:], strict=False):
        assert x1 <= nx0
    assert all(x0 >= 10 and x1 <= 190 for x0, _, x1, _ in rects)


def test_max_zero_does_not_divide_by_zero():
    rects = bar_geometry([0, 0, 0], width=100, height=100, padding=10)

    assert len(rects) == 3
    assert heights(rects) == [0, 0, 0]


def test_empty_list_returns_empty_list():
    assert bar_geometry([], width=100, height=100, padding=10) == []


def test_padding_larger_than_area_raises():
    with pytest.raises(ValueError):
        bar_geometry([1], width=20, height=100, padding=10)


def test_negative_values_are_treated_as_zero():
    rects = bar_geometry([-3, 4], width=100, height=100, padding=10)

    assert heights(rects) == [0, 80]


# ---- janela (smoke opt-in) ---------------------------------------------------


@pytest.mark.skipif(
    os.environ.get("POMODORO_UI_SMOKE") != "1",
    reason="smoke test de UI: defina POMODORO_UI_SMOKE=1 para executar",
)
def test_stats_window_smoke(storage: Storage):
    try:
        import customtkinter as ctk

        from pomodoro.ui.stats import StatsWindow
    except ImportError as exc:  # pragma: no cover
        pytest.skip(f"customtkinter indisponível: {exc}")

    seed(storage)
    try:
        root = ctk.CTk()
    except Exception as exc:  # sem display
        pytest.skip(f"sem display para a janela: {exc}")

    try:
        window = StatsWindow(root, storage, today=lambda: TODAY)
        root.update()
        assert window.winfo_exists()
        window.refresh()  # reabrir/atualizar não quebra
        window.destroy()
    finally:
        root.destroy()
