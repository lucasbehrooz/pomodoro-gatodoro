"""Persistência de sessões Pomodoro em SQLite (stdlib). Sem dependência de GUI.

Convenções:
- ``started_at`` é gravado em ISO 8601. Datas aware são convertidas para o
  horário local antes de gravar, então o prefixo ``YYYY-MM-DD`` sempre é o
  dia local. Datas naive são assumidas como horário local.
- Consultas por dia usam ``substr(started_at, 1, 10)``, evitando funções de
  data do SQLite que interpretariam offsets como UTC.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from types import TracebackType

from pomodoro.config import config_dir
from pomodoro.timer import Phase

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    phase TEXT NOT NULL,
    started_at TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    completed INTEGER NOT NULL CHECK (completed IN (0, 1))
);
CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON sessions (started_at);
"""

_DAY_SQL = "substr(started_at, 1, 10)"


def _local_iso(dt: datetime) -> str:
    if dt.tzinfo is not None:
        dt = dt.astimezone()  # converte para horário local, mantendo o offset
    return dt.isoformat()


class Storage:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (config_dir() / "pomodoro.db")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = sqlite3.connect(self.path)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # --- ciclo de vida -------------------------------------------------

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> Storage:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    @property
    def _db(self) -> sqlite3.Connection:
        if self._conn is None:
            raise sqlite3.ProgrammingError("Storage está fechado")
        return self._conn

    # --- escrita -------------------------------------------------------

    def record_session(
        self,
        phase: Phase,
        started_at: datetime,
        duration_seconds: int,
        completed: bool,
    ) -> None:
        if phase is Phase.IDLE:
            raise ValueError("Phase.IDLE não é uma sessão gravável")
        with self._db:
            self._db.execute(
                "INSERT INTO sessions (phase, started_at, duration_seconds, completed) "
                "VALUES (?, ?, ?, ?)",
                (phase.value, _local_iso(started_at), int(duration_seconds), int(completed)),
            )

    # --- leitura -------------------------------------------------------

    def count_completed_focus_between(self, start: date, end: date) -> int:
        """Focos concluídos com dia local em [start, end] (inclusivo)."""
        if start > end:
            raise ValueError("start deve ser <= end")
        row = self._db.execute(
            f"SELECT COUNT(*) FROM sessions "
            f"WHERE phase = ? AND completed = 1 AND {_DAY_SQL} BETWEEN ? AND ?",
            (Phase.FOCUS.value, start.isoformat(), end.isoformat()),
        ).fetchone()
        return int(row[0])

    def count_completed_focus(self, day: date) -> int:
        return self.count_completed_focus_between(day, day)

    def daily_focus_counts(self, start: date, end: date) -> dict[date, int]:
        """Focos concluídos por dia em [start, end]; dias sem registro valem 0."""
        if start > end:
            raise ValueError("start deve ser <= end")
        rows = self._db.execute(
            f"SELECT {_DAY_SQL} AS day, COUNT(*) FROM sessions "
            f"WHERE phase = ? AND completed = 1 AND {_DAY_SQL} BETWEEN ? AND ? "
            f"GROUP BY day",
            (Phase.FOCUS.value, start.isoformat(), end.isoformat()),
        ).fetchall()
        found = {date.fromisoformat(day): int(n) for day, n in rows}

        result: dict[date, int] = {}
        current = start
        while current <= end:
            result[current] = found.get(current, 0)
            current += timedelta(days=1)
        return result

    def today_count(self) -> int:
        return self.count_completed_focus(date.today())

    def week_count(self) -> int:
        """Focos concluídos na semana corrente (segunda a domingo)."""
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        return self.count_completed_focus_between(monday, monday + timedelta(days=6))
