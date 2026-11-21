"""Testes para F09: exportação CSV."""

from datetime import date, datetime
from pathlib import Path

import pytest

from pomodoro.export import sessions_to_csv
from pomodoro.storage import Storage
from pomodoro.timer import Phase


@pytest.fixture
def storage(tmp_path: Path) -> Storage:
    return Storage(tmp_path / "test.db")


def test_sessions_to_csv_header(storage: Storage) -> None:
    """CSV tem cabeçalho correto."""
    today = date.today()
    csv = sessions_to_csv(storage, today, today)
    lines = csv.split("\n")
    # Primeira linha é BOM + cabeçalho
    assert lines[0].startswith("\ufeff")
    assert "data,hora,fase,duração (min),concluída,tarefa" in lines[0]


def test_sessions_to_csv_with_data(storage: Storage) -> None:
    """CSV exporta sessões com dados corretos."""
    today = date.today()
    now_today = datetime.combine(today, datetime.min.time())

    storage.record_session(Phase.FOCUS, now_today, 1500, completed=True, task="Estudar")
    storage.record_session(Phase.SHORT_BREAK, now_today + __import__("datetime").timedelta(seconds=1500), 300, completed=True)

    csv = sessions_to_csv(storage, today, today)
    lines = csv.split("\n")
    
    # Deve ter cabeçalho + 2 sessões
    assert len(lines) >= 3
    # Segunda linha: foco concluído, 25 min (1500s), com tarefa
    assert "Estuar" not in lines[1]  # typo test
    assert "Sim" in lines[1]  # concluída
    assert "25" in lines[1]  # duração em min
    assert "Estudar" in lines[1]  # tarefa
    # Terceira linha: pausa concluída, 5 min, sem tarefa
    assert "short_break" in lines[2]
    assert "5" in lines[2]


def test_sessions_to_csv_escapes_quotes_in_task(storage: Storage) -> None:
    """Aspas duplas na tarefa são escapadas."""
    today = date.today()
    now = datetime.combine(today, datetime.min.time())
    
    storage.record_session(Phase.FOCUS, now, 600, completed=True, task='Tarefa com "aspas"')
    
    csv = sessions_to_csv(storage, today, today)
    # Escapado: "aspas" vira ""aspas""
    assert 'Tarefa com ""aspas""' in csv


def test_sessions_to_csv_utf8_bom(storage: Storage) -> None:
    """CSV começa com BOM UTF-8."""
    today = date.today()
    csv = sessions_to_csv(storage, today, today)
    assert csv.startswith("\ufeff")


def test_sessions_to_csv_acentos(storage: Storage) -> None:
    """Acentos no CSV são preservados."""
    today = date.today()
    now = datetime.combine(today, datetime.min.time())
    
    storage.record_session(Phase.FOCUS, now, 600, completed=True, task="Português: açúcar, café")
    
    csv = sessions_to_csv(storage, today, today)
    assert "Português: açúcar, café" in csv


def test_sessions_to_csv_empty(storage: Storage) -> None:
    """CSV sem sessões só tem cabeçalho."""
    today = date.today()
    csv = sessions_to_csv(storage, today, today)
    lines = [l for l in csv.split("\n") if l]
    assert len(lines) == 1  # só cabeçalho
