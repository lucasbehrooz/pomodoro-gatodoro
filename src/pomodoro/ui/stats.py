"""Tela de histórico e gráfico de pomodoros concluídos.

Parte pura (sem Tk, testável): build_week_series, summarize, bar_geometry.
Parte de janela: StatsWindow (CTkToplevel), aberta sob demanda pela MainWindow.

Contagem: só focos concluídos (completed=True), por dia local.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta
import tkinter as tk

import customtkinter as ctk

from pomodoro.storage import Storage
from pomodoro.ui.theme import (
    DEFAULT_THEME,
    Palette,
    apply_accent_button,
    apply_card,
    apply_text,
    apply_window,
    get_palette,
    refresh_transparent_bg,
)

CHART_DAYS = 7

# Geometria do gráfico (pixels). Padding também reserva espaço para rótulos.
CANVAS_WIDTH = 300
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


def summarize(storage: Storage, today: date) -> dict[str, int]:
    """Totais exibidos na tela.

    - today: focos concluídos em `today`.
    - week: focos na semana de `today` (segunda a domingo).
    - last_7_days: focos nos 7 dias terminando em `today`.
    """
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    series = build_week_series(storage, today, CHART_DAYS)
    return {
        "today": storage.count_completed_focus(today),
        "week": storage.count_completed_focus_between(monday, sunday),
        "last_7_days": sum(count for _, count in series),
    }


def bar_geometry(
    values: list[int], width: int, height: int, padding: int
) -> list[tuple[int, int, int, int]]:
    """Retângulos (x0, y0, x1, y1) das barras de um gráfico vertical.

    - As barras ficam sobre uma linha de base em `height - padding`.
    - A altura é proporcional ao maior valor (escala pelo máximo).
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
    peak = max(clamped)
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


# ---- janela -----------------------------------------------------------------

_LIGHT = {"bg": "#dbdbdb", "bar": "#3b8ed0", "text": "#000000"}
_DARK = {"bg": "#2b2b2b", "bar": "#3b8ed0", "text": "#ffffff"}


def chart_colors(palette: Palette, dark: bool) -> dict[str, str]:
    """Cores do gráfico para a paleta. ``dark`` é o modo do sistema (usado no tema padrão).

    Tema padrão (sem cores próprias): mantém as cores originais do gráfico.
    Demais temas: fundo do card, barras no accent e texto da paleta.
    """
    if palette.card is None or palette.accent is None or palette.text is None:
        return _DARK if dark else _LIGHT
    return {"bg": palette.card, "bar": palette.accent, "text": palette.text}


class StatsWindow(ctk.CTkToplevel):
    """Mostra totais e um gráfico de barras dos últimos 7 dias.

    `today` é injetável para testes; por padrão usa a data atual.
    Chama refresh() no construtor. Para atualizar uma janela já aberta, chame refresh().
    """

    def __init__(
        self,
        master: ctk.CTk,
        storage: Storage,
        today: Callable[[], date] = date.today,
        palette: Palette | None = None,
    ) -> None:
        super().__init__(master)
        self.title("Estatísticas")
        self.resizable(False, False)
        self.transient(master)

        self._storage = storage
        self._today = today
        self._palette: Palette = palette or get_palette(DEFAULT_THEME)

        self._frame = ctk.CTkFrame(self)
        frame = self._frame
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        self._today_label = ctk.CTkLabel(frame, text="", anchor="w")
        self._today_label.pack(anchor="w", pady=2)
        self._week_label = ctk.CTkLabel(frame, text="", anchor="w")
        self._week_label.pack(anchor="w", pady=2)
        self._last7_label = ctk.CTkLabel(frame, text="", anchor="w")
        self._last7_label.pack(anchor="w", pady=2)

        self._caption = ctk.CTkLabel(frame, text="Focos concluídos por dia (últimos 7 dias)")
        self._caption.pack(anchor="w", pady=(12, 4))
        self._canvas = tk.Canvas(
            frame,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack()

        self._close_btn = ctk.CTkButton(frame, text="Fechar", width=90, command=self.destroy)
        self._close_btn.pack(anchor="e", pady=(12, 0))

        self.apply_palette(self._palette)

    def apply_palette(self, palette: Palette) -> None:
        """Aplica a paleta à janela e redesenha o gráfico. Pode ser chamado a qualquer momento."""
        self._palette = palette
        apply_window(self, palette, "CTkToplevel")
        apply_card(self._frame, palette)
        for label in (self._today_label, self._week_label, self._last7_label):
            apply_text(label, palette)
        apply_text(self._caption, palette, muted=True)
        apply_accent_button(self._close_btn, palette)
        refresh_transparent_bg(self)
        self.refresh()

    def refresh(self) -> None:
        today = self._today()
        totals = summarize(self._storage, today)
        self._today_label.configure(text=f"Pomodoros hoje: {totals['today']}")
        self._week_label.configure(text=f"Na semana (seg a dom): {totals['week']}")
        self._last7_label.configure(text=f"Nos últimos 7 dias: {totals['last_7_days']}")

        series = build_week_series(self._storage, today, CHART_DAYS)
        self._draw_chart(series)

    # ---- internos ---------------------------------------------------------

    def _draw_chart(self, series: list[tuple[date, int]]) -> None:
        dark = ctk.get_appearance_mode() == "Dark"
        colors = chart_colors(self._palette, dark)
        canvas = self._canvas
        canvas.delete("all")
        canvas.configure(bg=colors["bg"])

        values = [count for _, count in series]
        rects = bar_geometry(values, CANVAS_WIDTH, CANVAS_HEIGHT, CANVAS_PADDING)
        base = CANVAS_HEIGHT - CANVAS_PADDING
        canvas.create_line(
            CANVAS_PADDING // 2,
            base,
            CANVAS_WIDTH - CANVAS_PADDING // 2,
            base,
            fill=colors["text"],
        )

        for (day, count), (x0, y0, x1, y1) in zip(series, rects, strict=True):
            cx = (x0 + x1) / 2
            if y1 > y0:
                canvas.create_rectangle(x0, y0, x1, y1, fill=colors["bar"], outline="")
            canvas.create_text(cx, y0 - 4, text=str(count), anchor="s", fill=colors["text"])
            canvas.create_text(
                cx, base + 12, text=f"{day:%d/%m}", anchor="center", fill=colors["text"]
            )
