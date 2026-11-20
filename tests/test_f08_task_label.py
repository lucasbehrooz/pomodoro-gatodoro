"""Testes para F08: rótulo da tarefa."""

from datetime import date, datetime, timedelta
import pytest
from pathlib import Path

from pomodoro.config import Config, load_config, save_config
from pomodoro.storage import Storage
from pomodoro.timer import Phase
from pomodoro.ui.stats import tasks_summary


@pytest.fixture
def storage(tmp_path: Path) -> Storage:
    return Storage(tmp_path / "test.db")


def test_record_session_with_task(storage: Storage) -> None:
    """Registra sessão com tarefa."""
    now = datetime.now()
    storage.record_session(Phase.FOCUS, now, 1500, completed=True, task="Estudar Python")
    # Sem erro, registro feito.
    assert storage.today_count() == 1


def test_record_session_without_task(storage: Storage) -> None:
    """Registra sessão sem tarefa (None)."""
    now = datetime.now()
    storage.record_session(Phase.FOCUS, now, 1500, completed=True)
    assert storage.today_count() == 1


def test_focus_seconds_by_task(storage: Storage) -> None:
    """Agrega segundos por tarefa."""
    today = date.today()
    now_today = datetime.combine(today, datetime.min.time())

    storage.record_session(Phase.FOCUS, now_today, 1500, completed=True, task="Estudar")
    storage.record_session(Phase.FOCUS, now_today + timedelta(seconds=1500), 900, completed=True, task="Estudar")
    storage.record_session(Phase.FOCUS, now_today + timedelta(seconds=2400), 1200, completed=True, task="Trabalho")
    storage.record_session(Phase.FOCUS, now_today + timedelta(seconds=3600), 600, completed=True)

    result = storage.focus_seconds_by_task(today, today)
    assert result["Estudar"] == 2400  # 1500 + 900
    assert result["Trabalho"] == 1200
    assert result["Sem rótulo"] == 600


def test_config_current_task_default() -> None:
    """current_task padrão é vazio."""
    cfg = Config()
    assert cfg.current_task == ""


def test_config_current_task_roundtrip(tmp_path: Path) -> None:
    """current_task persiste em JSON."""
    path = tmp_path / "config.json"
    cfg = Config(current_task="Meu projeto")
    save_config(cfg, path)
    loaded = load_config(path)
    assert loaded.current_task == "Meu projeto"


def test_config_current_task_invalid_fallback(tmp_path: Path) -> None:
    """current_task inválido (não string) usa padrão."""
    path = tmp_path / "config.json"
    path.write_text('{"current_task": 123}', encoding="utf-8")
    cfg = load_config(path)
    assert cfg.current_task == ""


def test_tasks_summary_empty(storage: Storage) -> None:
    """tasks_summary com zero tarefas retorna vazio."""
    today = date.today()
    summary = tasks_summary(storage, today, "7")
    assert summary == ""


def test_tasks_summary_with_tasks(storage: Storage) -> None:
    """tasks_summary formata tarefas ordenadas por tempo."""
    today = date.today()
    now_today = datetime.combine(today, datetime.min.time())

    storage.record_session(Phase.FOCUS, now_today, 3600, completed=True, task="Estudar")  # 60m
    storage.record_session(Phase.FOCUS, now_today + timedelta(seconds=1), 1800, completed=True, task="Trabalho")  # 30m
    storage.record_session(Phase.FOCUS, now_today + timedelta(seconds=2), 600, completed=True)  # 10m, "Sem rótulo"

    summary = tasks_summary(storage, today, "7")
    lines = summary.split("\n")
    assert lines[0] == "Tempo por tarefa:"
    assert "Estudar: 60m" in summary
    assert "Trabalho: 30m" in summary
    assert "Sem rótulo: 10m" in summary
    # Ordem: maior tempo primeiro
    assert summary.index("Estudar") < summary.index("Trabalho")
    assert summary.index("Trabalho") < summary.index("Sem rótulo")
