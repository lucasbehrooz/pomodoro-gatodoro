"""Janela principal (CustomTkinter). Traduz eventos em chamadas ao PomodoroController.

Threading: todos os métodos de janela devem rodar na thread do Tk. Outras
threads (ex.: pystray) devem usar ``post(fn)``, que enfileira a chamada e a
executa no próximo tick da UI.
"""

from __future__ import annotations

import logging
import queue
from collections.abc import Callable

import customtkinter as ctk

from pomodoro.config import Config, save_config
from pomodoro.storage import Storage
from pomodoro.ui.controller import ApplyStatus, PomodoroController, format_mmss
from pomodoro.ui.settings_dialog import SettingsDialog
from pomodoro.ui.stats import StatsWindow

logger = logging.getLogger(__name__)

TICK_MS = 200

MSG_SETTINGS_APPLIED = "Configurações salvas e aplicadas."
MSG_SETTINGS_DEFERRED = (
    "Configurações salvas. Durações e ciclos serão aplicados ao reiniciar o ciclo."
)
MSG_PENDING_NOTICE = "Novas durações serão aplicadas ao reiniciar."
MSG_STATS_UNAVAILABLE = "Estatísticas indisponíveis: armazenamento não informado."


class MainWindow(ctk.CTk):
    """Janela principal.

    Parâmetros:
        controller: PomodoroController já construído.
        on_hide_to_tray: chamado ao fechar com close_to_tray ligado. Default: withdraw().
        on_quit: hook opcional executado antes de destruir a janela (ex.: parar a bandeja).
        can_hide_to_tray: se False, fechar a janela encerra o app mesmo com
            close_to_tray ligado (evita esconder a janela sem como reabri-la).
        save: função de persistência da configuração. Default: save_config.
    """

    def __init__(
        self,
        controller: PomodoroController,
        *,
        on_hide_to_tray: Callable[[], None] | None = None,
        on_quit: Callable[[], None] | None = None,
        can_hide_to_tray: bool = True,
        save: Callable[[Config], None] = save_config,
        storage: Storage | None = None,
    ) -> None:
        super().__init__()
        self._controller = controller
        self._on_hide_to_tray = on_hide_to_tray
        self._on_quit = on_quit
        self._can_hide_to_tray = can_hide_to_tray
        self._save = save
        self._storage = storage
        self._ui_queue: queue.Queue[Callable[[], None]] = queue.Queue()
        self._tick_after_id: str | None = None
        self._settings_dialog: SettingsDialog | None = None
        self._stats_window: StatsWindow | None = None
        self._quitting = False

        self.title("Pomodoro")
        self.geometry("340x440")
        self.resizable(False, False)
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close_requested)

        self._refresh()
        self._schedule_tick()

    # ---- construção -----------------------------------------------------

    def _build(self) -> None:
        self._phase_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=20, weight="bold"))
        self._phase_label.pack(pady=(24, 4))

        self._time_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=56, weight="bold"))
        self._time_label.pack(pady=4)

        self._cycle_label = ctk.CTkLabel(self, text="")
        self._cycle_label.pack(pady=4)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(pady=16)
        self._toggle_btn = ctk.CTkButton(buttons, text="Iniciar", width=100, command=self._on_toggle)
        self._toggle_btn.grid(row=0, column=0, padx=4)
        self._reset_btn = ctk.CTkButton(buttons, text="Reiniciar", width=100, command=self._on_reset)
        self._reset_btn.grid(row=0, column=1, padx=4)
        self._skip_btn = ctk.CTkButton(buttons, text="Pular", width=100, command=self._on_skip)
        self._skip_btn.grid(row=0, column=2, padx=4)

        self._pending_label = ctk.CTkLabel(self, text="", text_color="#f0ad4e")
        self._pending_label.pack(pady=(4, 0))
        self._status_label = ctk.CTkLabel(self, text="", wraplength=300)
        self._status_label.pack(pady=(4, 0))

        ctk.CTkButton(
            self, text="Configurações", width=160, command=self._open_settings
        ).pack(side="bottom", pady=16)
        ctk.CTkButton(
            self, text="Estatísticas", width=160, command=self._open_stats
        ).pack(side="bottom", pady=(0, 0))

    # ---- ações de usuário -----------------------------------------------

    def _on_toggle(self) -> None:
        self._controller.toggle()
        self._refresh()

    def _on_reset(self) -> None:
        self._controller.reset()
        self._refresh()

    def _on_skip(self) -> None:
        self._controller.skip()
        self._refresh()

    def _open_settings(self) -> None:
        dialog = self._settings_dialog
        if dialog is not None and dialog.winfo_exists():
            dialog.focus()
            return
        self._settings_dialog = SettingsDialog(
            self, self._controller.config, on_save=self._save_settings
        )

    def _open_stats(self) -> None:
        if self._storage is None:
            self._status_label.configure(text=MSG_STATS_UNAVAILABLE)
            return
        window = self._stats_window
        if window is not None and window.winfo_exists():
            window.refresh()
            window.deiconify()
            window.lift()
            window.focus()
            return
        self._stats_window = StatsWindow(self, self._storage)

    def _save_settings(self, new: Config) -> None:
        self._save(new)  # OSError é tratado pelo diálogo
        status = self._controller.apply_config(new)
        message = MSG_SETTINGS_APPLIED if status is ApplyStatus.APPLIED else MSG_SETTINGS_DEFERRED
        self._status_label.configure(text=message)
        self._refresh()

    def _on_close_requested(self) -> None:
        if self._controller.config.close_to_tray and self._can_hide_to_tray:
            self.hide_to_tray()
        else:
            self.quit_app()

    # ---- API para a bandeja (thread do Tk) ------------------------------

    @property
    def controller(self) -> PomodoroController:
        return self._controller

    def show_window(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()

    def hide_to_tray(self) -> None:
        if self._on_hide_to_tray is not None:
            self._on_hide_to_tray()
        else:
            self.withdraw()

    def quit_app(self) -> None:
        if self._quitting:
            return
        self._quitting = True
        if self._tick_after_id is not None:
            self.after_cancel(self._tick_after_id)
            self._tick_after_id = None
        self._controller.shutdown()
        if self._on_quit is not None:
            try:
                self._on_quit()
            except Exception:
                logger.exception("Falha no on_quit")
        self.destroy()

    def post(self, fn: Callable[[], None]) -> None:
        """Enfileira fn para execução na thread do Tk. Seguro de outras threads."""
        self._ui_queue.put(fn)

    # ---- loop de atualização --------------------------------------------

    def _schedule_tick(self) -> None:
        self._tick_after_id = self.after(TICK_MS, self._on_tick)

    def _on_tick(self) -> None:
        self._tick_after_id = None
        self._drain_queue()
        if self._quitting:
            return
        self._controller.tick()
        self._refresh()
        self._schedule_tick()

    def _drain_queue(self) -> None:
        while True:
            try:
                fn = self._ui_queue.get_nowait()
            except queue.Empty:
                return
            try:
                fn()
            except Exception:
                logger.exception("Falha em chamada enfileirada na UI")

    def _refresh(self) -> None:
        c = self._controller
        self._phase_label.configure(text=c.phase_label)
        self._time_label.configure(text=format_mmss(c.remaining_seconds))
        self._cycle_label.configure(
            text=f"Focos no ciclo: {c.completed_focus_count}/{c.cycles_before_long_break}"
        )
        self._toggle_btn.configure(text="Pausar" if c.is_running else "Iniciar")
        self._pending_label.configure(text=MSG_PENDING_NOTICE if c.timer_config_pending else "")
