"""Exportação de dados do histórico para CSV."""

from __future__ import annotations

from datetime import date, datetime

from pomodoro.storage import Storage


def sessions_to_csv(storage: Storage, start: date, end: date) -> str:
    """Gera CSV com histórico de sessões: data, hora, fase, duração (min), concluída, tarefa.

    Retorna string UTF-8 com BOM (\\ufeff) para Excel interpretar corretamente.
    Ordem: cronológica ascendente (mais antigo primeiro).
    """
    rows = storage._db.execute(
        f"SELECT started_at, phase, duration_seconds, completed, task "
        f"FROM sessions "
        f"WHERE substr(started_at, 1, 10) BETWEEN ? AND ? "
        f"ORDER BY started_at",
        (start.isoformat(), end.isoformat()),
    ).fetchall()

    lines = ["data,hora,fase,duração (min),concluída,tarefa"]
    for started_at_str, phase_val, seconds, completed, task in rows:
        dt = datetime.fromisoformat(started_at_str)
        data = dt.date().isoformat()
        hora = dt.time().isoformat()[:5]  # HH:MM
        minutos = seconds // 60
        sim_nao = "Sim" if completed else "Não"
        # Escapar aspas duplas no CSV: " vira ""
        tarefa = (task or "").replace('"', '""')
        lines.append(f'{data},{hora},{phase_val},{minutos},{sim_nao},"{tarefa}"')

    # BOM UTF-8: \\ufeff força Excel a ler como UTF-8 em vez de cp1252
    csv_str = "\n".join(lines)
    return "\ufeff" + csv_str
