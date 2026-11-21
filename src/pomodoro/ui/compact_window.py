"""Janela compacta: sempre no topo, só timer e botões Iniciar/Pausar."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import customtkinter as ctk

from pomodoro.ui.theme import Palette, apply_accent_button, apply_text, apply_window

if TYPE_CHECKING:
    from pomodoro.ui.controller import PomodoroController


class CompactWindow(ctk.CTkToplevel):
    """Janela compacta do Pomodoro: timer + 2 botões (Iniciar/Pausar, Sair)."""

    def __init__(self, controller: PomodoroController, palette: Palette) -> None:
        super().__init__()
        self.title("Pomodoro")
        self.geometry("300x120")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self._controller = controller
        self._palette = palette

        # Timer display
        self._timer_label = ctk.CTkLabel(
            self, text="00:00", font=ctk.CTkFont(family="Courier", size=48, weight="bold")
        )
        self._timer_label.pack(pady=10)

        # Botões (Iniciar/Pausar, Sair)
        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(pady=10)

        self._toggle_btn = ctk.CTkButton(
            buttons, text="Iniciar", width=80, command=self._on_toggle
        )
        self._toggle_btn.pack(side="left", padx=4)

        self._exit_btn = ctk.CTkButton(
            buttons, text="Sair", width=60, command=self._on_exit
        )
        self._exit_btn.pack(side="left", padx=4)

        self.apply_palette(palette)
        self._refresh()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_toggle(self) -> None:
        """Inicia/pausa timer."""
        self._controller.toggle()
        self._refresh()

    def _on_exit(self) -> None:
        """Volta para modo normal."""
        cfg = self._controller._config
        cfg.compact_mode = False
        self._controller._config_manager.save(cfg)
        self.destroy()
        from pomodoro.ui.main_window import MainWindow
        # MainWindow já existe, só deiconify
        self.master.deiconify() if hasattr(self, 'master') else None

    def _on_close(self) -> None:
        """Fecha janela compacta (volta para normal)."""
        self._on_exit()

    def _refresh(self) -> None:
        """Atualiza timer e estado botão."""
        c = self._controller.state()
        mm, ss = divmod(c.remaining_seconds, 60)
        self._timer_label.configure(text=f"{mm:02d}:{ss:02d}")
        self._toggle_btn.configure(
            text="Pausar" if c.is_running else "Iniciar"
        )

    def apply_palette(self, palette: Palette) -> None:
        """Aplica paleta."""
        apply_window(self, palette, "CTkToplevel")
        apply_text(self._timer_label, palette)
        apply_accent_button(self._toggle_btn, palette)
        apply_accent_button(self._exit_btn, palette)
