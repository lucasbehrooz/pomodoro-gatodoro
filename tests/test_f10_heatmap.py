"""Testes F10: mapa de calor do ano."""

from datetime import date

import pytest

from pomodoro.ui.stats import (
    heatmap_cells,
    heatmap_color_bucket,
    heatmap_grid_geometry,
    heatmap_minutes_by_day,
    heatmap_year_range,
)
from pomodoro.storage import Storage
from pomodoro.timer import Phase
from pathlib import Path


@pytest.fixture
def storage(tmp_path: Path) -> Storage:
    return Storage(tmp_path / "test.db")


def test_heatmap_year_range() -> None:
    """Intervalo começa no dia 1 do ano."""
    today = date(2024, 6, 15)
    start, end = heatmap_year_range(today)
    assert start == date(2024, 1, 1)
    assert end == today


def test_heatmap_grid_geometry() -> None:
    """Dimensões grid 53×7."""
    geom = heatmap_grid_geometry(cell_size=10, gap=2, padding=5)
    # 53 cols: 53*10 + 52*2 = 530+104 = 634
    # 7 rows: 7*10 + 6*2 = 70+12 = 82
    assert geom["width"] == 634 + 10  # padding *2
    assert geom["height"] == 82 + 10


def test_heatmap_cells_count_2024() -> None:
    """2024 é bissexto: 366 dias."""
    cells = heatmap_cells(year=2024, cell_size=10, gap=2, padding=5)
    # Células do ano 2024
    cells_2024 = [c for c in cells if c[0].year == 2024]
    assert len(cells_2024) == 366


def test_heatmap_cells_jan1_position() -> None:
    """Jan 1, 2024 está em posição correta (segunda=0, domingo=6)."""
    cells = heatmap_cells(year=2024, cell_size=10, gap=2, padding=5)
    # Jan 1, 2024 é segunda-feira
    jan1_cell = [c for c in cells if c[0] == date(2024, 1, 1)][0]
    # row deve ser 0 (segunda)
    row = (jan1_cell[2] - 5) // (10 + 2)  # (y0 - padding) / (size + gap)
    assert row == 0


def test_heatmap_color_bucket_ranges() -> None:
    """Faixas de cor: 0, 1-50, 51-150, 151-300, 300+."""
    assert heatmap_color_bucket(0) == 0
    assert heatmap_color_bucket(25) == 1
    assert heatmap_color_bucket(50) == 1
    assert heatmap_color_bucket(51) == 2
    assert heatmap_color_bucket(150) == 2
    assert heatmap_color_bucket(151) == 3
    assert heatmap_color_bucket(300) == 3
    assert heatmap_color_bucket(301) == 4




def test_heatmap_minutes_by_day_with_data(storage: Storage) -> None:
    """Agregação de minutos por dia."""
    from datetime import datetime
    
    day1 = date(2024, 1, 15)
    now = datetime.combine(day1, datetime.min.time())
    
    # Dois focos no mesmo dia: 25 + 20 = 45 min
    storage.record_session(Phase.FOCUS, now, 1500, completed=True)
    storage.record_session(Phase.FOCUS, now.replace(hour=2), 1200, completed=True)
    
    minutes = heatmap_minutes_by_day(storage, day1, day1)
    assert minutes.get(day1) == 45
