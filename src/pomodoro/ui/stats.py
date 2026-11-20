"""Tela de histórico e gráfico de pomodoros concluídos.

Parte pura (sem Tk, testável): build_week_series, summarize, bar_geometry, goal_line_y.
Parte de janela: StatsWindow (CTkToplevel), aberta sob demanda pela MainWindow.

Contagem: só focos concluídos (completed=True), por dia local.
Tempo: soma de todo o foco, inclusive focos interrompidos.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import date, timedelta
import math
import tkinter as tk

import customtkinter as ctk

from pomodoro.ui.icon import apply_window_icon

from pomodoro.storage import Storage
from pomodoro.ui.theme import (
    CHART_GOAL_DARK,
    CHART_GOAL_LIGHT,
    DEFAULT_THEME,
    Palette,
    goal_line_color,
    apply_accent_button,
    apply_card,
    apply_option_menu,
    apply_text,
    apply_window,
    get_palette,
    refresh_transparent_bg,
)

CHART_DAYS = 7

# Períodos disponíveis no seletor: rótulo -> chave interna.
PERIOD_LABELS: dict[str, str] = {
    "7 dias": "7",
    "30 dias": "30",
    "Mês atual": "month",
}
DEFAULT_PERIOD = "7"

# O que o gráfico mostra: rótulo -> chave interna.
METRIC_LABELS: dict[str, str] = {
    "Pomodoros": "count",
    "Tempo": "time",
}
DEFAULT_METRIC = "count"
MAX_X_LABELS = 7  # quantidade máxima de datas no eixo X

# Geometria do gráfico (pixels). Padding também reserva espaço para rótulos.
CANVAS_WIDTH = 320
CANVAS_HEIGHT = 200
CANVAS_PADDING = 28
BAR_FILL_RATIO = 0.6  # fração do espaço de cada coluna ocupada pela barra


# ---- parte pura -------------------------------------------------------------


def build_week_series(
    storage: Storage, today: date, days: int = CHART_DAYS
) -> list[tuple[date, int]]:
    """Focos concluídos por dia nos últimos `days` dias, incluindo `today`.

    Retorna em ordem cronológica (mais antigo primeiro). Dias sem registro
    aparecem com contagem 0.
    """
    if days < 1:
        raise ValueError("days deve ser >= 1")
    start = today - timedelta(days=days - 1)
    counts = storage.daily_focus_counts(start, today)
    return [(day, counts[day]) for day in sorted(counts)]


def format_duration(seconds: int) -> str:
    """Tempo legível: '0 min', '45 min', '1h', '2h 5min'. Segundos são descartados."""
    minutes = max(0, int(seconds)) // 60
    hours, minutes = divmod(minutes, 60)
    if hours == 0:
        return f"{minutes} min"
    if minutes == 0:
        return f"{hours}h"
    return f"{hours}h {minutes}min"


def summarize(storage: Storage, today: date) -> dict[str, int]:
    """Totais exibidos na tela.

    - today: focos concluídos em `today`.
    - week: focos na semana de `today` (segunda a domingo).
    - last_7_days: focos nos 7 dias terminando em `today`.
    - today_seconds / week_seconds: tempo de foco nos mesmos intervalos.
    """
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    series = build_week_series(storage, today, CHART_DAYS)
    return {
        "today": storage.count_completed_focus(today),
        "week": storage.count_completed_focus_between(monday, sunday),
        "last_7_days": sum(count for _, count in series),
        "today_seconds": storage.focus_seconds_between(today, today),
        "week_seconds": storage.focus_seconds_between(monday, sunday),
    }


def period_range(period: str, today: date) -> tuple[date, date]:
    """Intervalo inclusivo [início, fim] de um período do seletor.

    - "7" / "30": últimos N dias terminando em `today`.
    - "month": do dia 1 do mês de `today` até `today`.
    """
    if period == "month":
        return today.replace(day=1), today
    if period.isdigit() and int(period) >= 1:
        return today - timedelta(days=int(period) - 1), today
    raise ValueError(f"período desconhecido: {period!r}")


def build_period_series(
    storage: Storage, today: date, period: str, metric: str = "count"
) -> list[tuple[date, int]]:
    """Valores por dia no período, em ordem cronológica, com zeros.

    metric "count": focos concluídos. metric "time": segundos de foco.
    """
    start, end = period_range(period, today)
    if metric == "count":
        values = storage.daily_focus_counts(start, end)
    elif metric == "time":
        values = storage.daily_focus_seconds(start, end)
    else:
        raise ValueError(f"métrica desconhecida: {metric!r}")
    return [(day, values[day]) for day in sorted(values)]


def period_total(storage: Storage, today: date, period: str) -> int:
    """Total de focos concluídos no período."""
    start, end = period_range(period, today)
    return storage.count_completed_focus_between(start, end)


def period_seconds(storage: Storage, today: date, period: str) -> int:
    """Tempo total de foco no período, em segundos."""
    start, end = period_range(period, today)
    return storage.focus_seconds_between(start, end)


def format_duration_short(seconds: int) -> str:
    """Versão curta para cima das barras: '0', '25m', '1h', '1h05'."""
    minutes = max(0, int(seconds)) // 60
    hours, minutes = divmod(minutes, 60)
    if hours == 0:
        return f"{minutes}m" if minutes else "0"
    if minutes == 0:
        return f"{hours}h"
    return f"{hours}h{minutes:02d}"


def bar_label(value: int, metric: str) -> str:
    """Texto em cima de cada barra do gráfico."""
    return format_duration_short(value) if metric == "time" else str(value)


def stat_line(title: str, count: int, seconds: int) -> str:
    """Linha de total: 'Pomodoros hoje: 3 · 1h 15min de foco'."""
    return f"{title}: {count} · {format_duration(seconds)} de foco"


def streak(days: Iterable[date], today: date) -> int:
    """Dias seguidos com foco concluído até hoje.

    Conta `today` se ele estiver em `days`; senão a sequência termina ontem.
    Sem foco hoje nem ontem, a sequência é 0. Dias futuros são ignorados.
    """
    found = set(days)
    current = today if today in found else today - timedelta(days=1)
    count = 0
    while current in found:
        count += 1
        current -= timedelta(days=1)
    return count


def record_streak(days: Iterable[date]) -> int:
    """Maior sequência de dias seguidos com foco concluído em `days`."""
    best = run = 0
    previous: date | None = None
    for day in sorted(set(days)):
        run = run + 1 if previous is not None and day - previous == timedelta(days=1) else 1
        best = max(best, run)
        previous = day
    return best


def format_days(count: int) -> str:
    """'1 dia', '0 dias', '5 dias'."""
    return f"{count} dia" if count == 1 else f"{count} dias"


def streak_line(current: int, best: int) -> str:
    """Linha das Estatísticas: 'Sequência: 5 dias · Recorde: 12 dias'."""
    return f"Sequência: {format_days(current)} · Recorde: {format_days(best)}"


def label_step(count: int, max_labels: int = MAX_X_LABELS) -> int:
    """Passo entre datas exibidas no eixo X, para não sobrepor os rótulos."""
    if count <= max_labels:
        return 1
    return math.ceil(count / max_labels)


def chart_scale(values: list[int], goal: int = 0) -> int:
    """Valor que ocupa a altura toda do gráfico: o maior entre os valores e a meta."""
    return max([0, goal, *values])


def bar_geometry(
    values: list[int], width: int, height: int, padding: int, scale: int | None = None
) -> list[tuple[int, int, int, int]]:
    """Retângulos (x0, y0, x1, y1) das barras de um gráfico vertical.

    - As barras ficam sobre uma linha de base em `height - padding`.
    - A altura é proporcional ao maior valor (escala pelo máximo), ou a
      `scale` quando informado (ex.: para caber a linha da meta).
    - Valor zero, ou máximo zero, gera barra de altura 0 (y0 == y1 == base):
      nenhuma área é desenhada, mas a coluna continua reservada e o rótulo "0"
      continua visível na tela.
    - Valores negativos são tratados como 0.
    - Lista vazia retorna lista vazia.
    """
    if not values:
        return []
    inner_w = width - 2 * padding
    inner_h = height - 2 * padding
    if inner_w <= 0 or inner_h <= 0:
        raise ValueError("área insuficiente para o padding informado")

    clamped = [max(0, v) for v in values]
    peak = max(max(clamped), scale or 0)
    slot = inner_w / len(clamped)
    bar_w = max(1, int(slot * BAR_FILL_RATIO))
    base = height - padding

    rects: list[tuple[int, int, int, int]] = []
    for index, value in enumerate(clamped):
        center = padding + slot * (index + 0.5)
        x0 = round(center - bar_w / 2)
        bar_h = 0 if peak == 0 else round(value / peak * inner_h)
        rects.append((x0, base - bar_h, x0 + bar_w, base))
    return rects


def goal_line_y(goal: int, scale: int, height: int, padding: int) -> int | None:
    """Altura (y) da linha da meta no gráfico, na mesma escala das barras.

    None quando não há meta (goal <= 0) ou escala; o gráfico então não mostra a linha.
    """
    if goal <= 0 or scale <= 0:
        return None
    inner_h = height - 2 * padding
    if inner_h <= 0:
        raise ValueError("área insuficiente para o padding informado")
    base = height - padding
    return base - round(min(goal, scale) / scale * inner_h)


def show_goal_line(metric: str, goal: int) -> bool:
    """A linha da meta só faz sentido no gráfico de quantidade e com meta ligada."""
    return metric == "count" and goal > 0


def goal_legend_text(metric: str, goal: int) -> str:
    """Legenda da linha da meta, exibida abaixo do gráfico (fora da área das barras).

    Fica fora do canvas para nunca cobrir o número em cima de uma barra que
    bateu a meta. Vazia quando a linha não aparece.
    """
    if not show_goal_line(metric, goal):
        return ""
    return f"- - -  Meta diária: {goal}"


def tasks_summary(storage: Storage, today: date, period: str) -> str:
    """Resumo de tempo por tarefa no período. Ordenado por tempo decrescente."""
    start, end = period_range(period, today)
    tasks = storage.focus_seconds_by_task(start, end)
    if not tasks:
        return ""
    lines = ["Tempo por tarefa:"]
    for task_label, seconds in tasks.items():
        minutes = seconds // 60
        lines.append(f"  {task_label}: {minutes}m")
    return "\n".join(lines)


# ---- janela -----------------------------------------------------------------

_LIGHT = {"bg": "#dbdbdb", "bar": "#3b8ed0", "text": "#000000", "goal": CHART_GOAL_LIGHT}
_DARK = {"bg": "#2b2b2b", "bar": "#3b8ed0", "text": "#ffffff", "goal": CHART_GOAL_DARK}


def chart_colors(palette: Palette, dark: bool) -> dict[str, str]:
    """Cores do gráfico para a paleta. ``dark`` é o modo do sistema (usado no tema padrão).

    Tema padrão (sem cores próprias): mantém as cores originais do gráfico.
    Demais temas: fundo do card, barras no accent e texto da paleta.
    """
    if (
        palette.card is None
        or palette.accent is None
        or palette.text is None
        or palette.goal_line is None
    ):
        return _DARK if dark else _LIGHT
    return {
        "bg": palette.card,
        "bar": palette.accent,
        "text": palette.text,
        "goal": palette.goal_line,
    }


def _key_label(labels: dict[str, str], key: str) -> str:
    return next(label for label, k in labels.items() if k == key)


class StatsWindow(ctk.CTkToplevel):
    """Mostra totais e um gráfico de barras dos últimos 7 dias.

    `today` é injetável para testes; por padrão usa a data atual.
    `goal` devolve a meta diária atual (0 = sem linha da meta); é lida a cada
    refresh, então mudar a meta nas Configurações vale na próxima atualização.
    Chama refresh() no construtor. Para atualizar uma janela já aberta, chame refresh().
    """

    def __init__(
        self,
        master: ctk.CTk,
        storage: Storage,
        today: Callable[[], date] = date.today,
        palette: Palette | None = None,
        goal: Callable[[], int] = lambda: 0,
    ) -> None:
        super().__init__(master)
        self.title("Estatísticas")
        apply_window_icon(self)
        self.resizable(False, False)
        self.transient(master)

        self._storage = storage
        self._today = today
        self._goal = goal
        self._palette: Palette = palette or get_palette(DEFAULT_THEME)

        self._frame = ctk.CTkFrame(self)
        frame = self._frame
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        self._today_label = ctk.CTkLabel(frame, text="", anchor="w")
        self._today_label.pack(anchor="w", pady=2)
        self._week_label = ctk.CTkLabel(frame, text="", anchor="w")
        self._week_label.pack(anchor="w", pady=2)
        self._period_label = ctk.CTkLabel(frame, text="", anchor="w")
        self._period_label.pack(anchor="w", pady=2)
        self._streak_label = ctk.CTkLabel(frame, text="", anchor="w")
        self._streak_label.pack(anchor="w", pady=2)
        self._tasks_label = ctk.CTkLabel(frame, text="", anchor="w", justify="left")
        self._tasks_label.pack(anchor="w", pady=2)

        selectors = ctk.CTkFrame(frame, fg_color="transparent")
        selectors.pack(anchor="w", pady=(8, 0))
        self._period_key = DEFAULT_PERIOD
        self._period_menu = ctk.CTkOptionMenu(
            selectors,
            values=list(PERIOD_LABELS),
            command=self._on_period_selected,
            width=140,
        )
        self._period_menu.set(self._label_for(self._period_key))
        self._period_menu.pack(side="left")
        self._metric_key = DEFAULT_METRIC
        self._metric_menu = ctk.CTkOptionMenu(
            selectors,
            values=list(METRIC_LABELS),
            command=self._on_metric_selected,
            width=130,
        )
        self._metric_menu.set(_key_label(METRIC_LABELS, self._metric_key))
        self._metric_menu.pack(side="left", padx=(8, 0))

        self._caption = ctk.CTkLabel(frame, text="")
        self._caption.pack(anchor="w", pady=(8, 4))
        self._canvas = tk.Canvas(
            frame,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack()
        # Legenda da linha da meta: empacotada só quando a linha aparece.
        self._goal_legend = ctk.CTkLabel(frame, text="", anchor="w")

        self._close_btn = ctk.CTkButton(frame, text="Fechar", width=90, command=self.destroy)
        self._close_btn.pack(anchor="e", pady=(12, 0))

        self.apply_palette(self._palette)

    def apply_palette(self, palette: Palette) -> None:
        """Aplica a paleta à janela e redesenha o gráfico. Pode ser chamado a qualquer momento."""
        self._palette = palette
        apply_window(self, palette, "CTkToplevel")
        apply_card(self._frame, palette)
        for label in (
            self._today_label,
            self._week_label,
            self._period_label,
            self._streak_label,
            self._tasks_label,
        ):
            apply_text(label, palette)
        apply_text(self._caption, palette, muted=True)
        self._goal_legend.configure(text_color=goal_line_color(palette))
        apply_option_menu(self._period_menu, palette)
        apply_option_menu(self._metric_menu, palette)
        apply_accent_button(self._close_btn, palette)
        refresh_transparent_bg(self)
        self.refresh()

    def refresh(self) -> None:
        today = self._today()
        totals = summarize(self._storage, today)
        self._today_label.configure(
            text=stat_line("Pomodoros hoje", totals["today"], totals["today_seconds"])
        )
        self._week_label.configure(
            text=stat_line("Na semana (seg a dom)", totals["week"], totals["week_seconds"])
        )

        period = self._period_key
        total = period_total(self._storage, today, period)
        seconds = period_seconds(self._storage, today, period)
        self._period_label.configure(text=stat_line(self._period_title(), total, seconds))
        what = "Tempo de foco" if self._metric_key == "time" else "Focos concluídos"
        self._caption.configure(text=f"{what} por dia ({self._period_title().lower()})")

        days = self._storage.completed_focus_days()
        self._streak_label.configure(text=streak_line(streak(days, today), record_streak(days)))
        self._tasks_label.configure(text=tasks_summary(self._storage, today, self._period_key))

        series = build_period_series(self._storage, today, period, self._metric_key)
        self._draw_chart(series)
        self._sync_goal_legend()

    # ---- internos ---------------------------------------------------------

    def _label_for(self, key: str) -> str:
        return _key_label(PERIOD_LABELS, key)

    def _period_title(self) -> str:
        if self._period_key == "month":
            return "No mês"
        return f"Nos últimos {self._period_key} dias"

    def _on_period_selected(self, label: str) -> None:
        self._period_key = PERIOD_LABELS[label]
        self.refresh()

    def _on_metric_selected(self, label: str) -> None:
        self._metric_key = METRIC_LABELS[label]
        self.refresh()

    def _sync_goal_legend(self) -> None:
        text = goal_legend_text(self._metric_key, self._goal())
        self._goal_legend.configure(text=text)
        if text and not self._goal_legend.winfo_manager():
            self._goal_legend.pack(anchor="w", pady=(4, 0), before=self._close_btn)
        elif not text and self._goal_legend.winfo_manager():
            self._goal_legend.pack_forget()

    def _draw_chart(self, series: list[tuple[date, int]]) -> None:
        dark = ctk.get_appearance_mode() == "Dark"
        colors = chart_colors(self._palette, dark)
        canvas = self._canvas
        canvas.delete("all")
        canvas.configure(bg=colors["bg"])

        values = [count for _, count in series]
        goal = self._goal()
        if not show_goal_line(self._metric_key, goal):
            goal = 0
        scale = chart_scale(values, goal)
        rects = bar_geometry(values, CANVAS_WIDTH, CANVAS_HEIGHT, CANVAS_PADDING, scale)
        base = CANVAS_HEIGHT - CANVAS_PADDING
        canvas.create_line(
            CANVAS_PADDING // 2,
            base,
            CANVAS_WIDTH - CANVAS_PADDING // 2,
            base,
            fill=colors["text"],
        )
        goal_y = goal_line_y(goal, scale, CANVAS_HEIGHT, CANVAS_PADDING)
        if goal_y is not None:
            # Tracejada e explicada pela legenda abaixo do gráfico (não só pela cor).
            # Desenhada antes das barras e dos números, que ficam por cima dela.
            # Sem texto no canvas: nada cobre o número das barras.
            canvas.create_line(
                CANVAS_PADDING // 2,
                goal_y,
                CANVAS_WIDTH - CANVAS_PADDING // 2,
                goal_y,
                fill=colors["goal"],
                dash=(4, 3),
                width=2,
                tags=("goal_line",),
            )

        step = label_step(len(series))
        for index, ((day, count), (x0, y0, x1, y1)) in enumerate(zip(series, rects, strict=True)):
            cx = (x0 + x1) / 2
            if y1 > y0:
                canvas.create_rectangle(x0, y0, x1, y1, fill=colors["bar"], outline="")
            # Valor em cima da barra só quando há espaço (poucos dias).
            if len(series) <= 14:
                canvas.create_text(
                    cx, y0 - 4, text=bar_label(count, self._metric_key), anchor="s",
                    fill=colors["text"],
                )
            if index % step == 0:
                canvas.create_text(
                    cx, base + 12, text=f"{day:%d/%m}", anchor="center", fill=colors["text"]
                )

