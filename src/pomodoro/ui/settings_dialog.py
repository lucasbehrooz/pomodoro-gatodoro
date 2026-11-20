"""Diálogo de configurações (CTkToplevel). Valida via settings.build_config."""

from __future__ import annotations

import logging
import webbrowser
from collections.abc import Callable

import customtkinter as ctk

from pomodoro.ui.icon import apply_window_icon

from pomodoro import __version__
from pomodoro.config import Config
from pomodoro.updater import UpdateManager, UpdateState, format_progress
from pomodoro.ui.settings import (
    BOOL_FIELDS,
    INT_FIELDS,
    LABELS,
    SettingsError,
    build_config,
    form_values,
)
from pomodoro.ui.theme import (
    THEME_LABELS,
    Palette,
    apply_accent_button,
    apply_card,
    apply_checkbox,
    apply_entry,
    apply_option_menu,
    apply_slider,
    apply_text,
    apply_window,
    get_palette,
    refresh_transparent_bg,
    theme_key_from_label,
    theme_label,
)


logger = logging.getLogger(__name__)

UPDATE_MESSAGES: dict[UpdateState, str] = {
    UpdateState.IDLE: "",
    UpdateState.CHECKING: "Verificando…",
    UpdateState.UP_TO_DATE: "Você está na versão mais recente.",
    UpdateState.LAUNCHING: "Abrindo o instalador… o app vai fechar.",
}


def update_status_text(updates: UpdateManager) -> str:
    """Texto da linha de status da seção Atualizações."""
    state = updates.state
    if state is UpdateState.AVAILABLE and updates.info is not None:
        return f"Nova versão disponível: {updates.info.version}"
    if state is UpdateState.DOWNLOADING:
        return format_progress(*updates.progress)
    if state is UpdateState.ERROR:
        return updates.error
    return UPDATE_MESSAGES.get(state, "")


class SettingsDialog(ctk.CTkToplevel):
    """Coleta os valores e chama on_save(new_config).

    on_save persiste e aplica a configuração (ex.: save_config + apply_config).
    Pode lançar OSError (falha ao salvar), que é mostrada no diálogo sem fechá-lo.

    Trocar o tema no seletor só pré-visualiza as cores neste diálogo. A troca
    vale para o app inteiro apenas quando o usuário clica em "Salvar".
    """

    def __init__(
        self,
        master: ctk.CTk,
        config: Config,
        on_save: Callable[[Config], None],
        updates: UpdateManager | None = None,
        open_url: Callable[[str], object] = webbrowser.open,
    ) -> None:
        super().__init__(master)
        self.title("Configurações")
        apply_window_icon(self)
        self.resizable(False, False)
        self.transient(master)

        self._base = config
        self._on_save = on_save
        self._updates = updates
        self._open_url = open_url
        self._palette: Palette = get_palette(config.theme)
        values = form_values(config)

        self._frame = ctk.CTkFrame(self)
        self._frame.pack(fill="both", expand=True, padx=16, pady=16)
        frame = self._frame

        self._labels: list[ctk.CTkLabel] = []
        self._entries: dict[str, ctk.CTkEntry] = {}
        row = 0
        for name in INT_FIELDS:
            self._add_label(frame, LABELS[name], row)
            entry = ctk.CTkEntry(frame, width=80)
            entry.insert(0, str(values[name]))
            entry.grid(row=row, column=1, sticky="e", pady=4)
            self._entries[name] = entry
            row += 1

        self._add_label(frame, LABELS["brown_noise_volume"], row)
        self._volume = ctk.CTkSlider(frame, from_=0, to=100, number_of_steps=100, width=160)
        self._volume.set(float(values["brown_noise_volume"]))  # type: ignore[arg-type]
        self._volume.grid(row=row, column=1, sticky="e", pady=4)
        row += 1

        self._add_label(frame, LABELS["theme"], row)
        self._theme_menu = ctk.CTkOptionMenu(
            frame,
            values=list(THEME_LABELS.values()),
            width=160,
            command=self._on_theme_selected,
        )
        self._theme_menu.set(theme_label(config.theme))
        self._theme_menu.grid(row=row, column=1, sticky="e", pady=4)
        row += 1

        self._bools: dict[str, ctk.BooleanVar] = {}
        self._checkboxes: list[ctk.CTkCheckBox] = []
        for name in BOOL_FIELDS:
            var = ctk.BooleanVar(value=bool(values[name]))
            box = ctk.CTkCheckBox(frame, text=LABELS[name], variable=var)
            box.grid(row=row, column=0, columnspan=2, sticky="w", pady=2)
            self._bools[name] = var
            self._checkboxes.append(box)
            row += 1

        if updates is not None:
            row = self._build_updates(frame, row)

        self._message = ctk.CTkLabel(frame, text="", wraplength=320)
        self._message.grid(row=row, column=0, columnspan=2, sticky="w", pady=(8, 0))
        row += 1

        buttons = ctk.CTkFrame(frame, fg_color="transparent")
        buttons.grid(row=row, column=0, columnspan=2, sticky="e", pady=(12, 0))
        self._cancel_btn = ctk.CTkButton(
            buttons, text="Cancelar", width=90, command=self.destroy
        )
        self._cancel_btn.pack(side="left", padx=(0, 8))
        self._save_btn = ctk.CTkButton(
            buttons, text="Salvar", width=90, command=self._save_clicked
        )
        self._save_btn.pack(side="left")

        self._apply_palette(self._palette)
        if updates is not None:
            updates.subscribe(self._sync_updates)
            self._sync_updates()

    def destroy(self) -> None:
        if self._updates is not None:
            self._updates.unsubscribe(self._sync_updates)
        super().destroy()

    # ---- atualizações -------------------------------------------------------

    def _build_updates(self, frame: ctk.CTkFrame, row: int) -> int:
        self._updates_title = ctk.CTkLabel(
            frame, text="Atualizações", anchor="w", font=ctk.CTkFont(weight="bold")
        )
        self._updates_title.grid(row=row, column=0, columnspan=2, sticky="w", pady=(12, 0))
        row += 1
        self._version_label = ctk.CTkLabel(
            frame, text=f"Versão instalada: {__version__}", anchor="w"
        )
        self._version_label.grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1
        self._update_status = ctk.CTkLabel(frame, text="", anchor="w", wraplength=320)
        self._update_status.grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1
        buttons = ctk.CTkFrame(frame, fg_color="transparent")
        buttons.grid(row=row, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self._check_btn = ctk.CTkButton(
            buttons, text="Verificar atualizações", width=160, command=self._on_check_updates
        )
        self._check_btn.pack(side="left", padx=(0, 8))
        self._install_btn = ctk.CTkButton(
            buttons, text="Atualizar", width=140, command=self._on_install_update
        )
        # _install_btn só é empacotado quando há versão nova (_sync_updates).
        return row + 1

    def _on_check_updates(self) -> None:
        if self._updates is not None:
            self._updates.check()

    def _on_install_update(self) -> None:
        updates = self._updates
        if updates is None or updates.info is None:
            return
        if not updates.info.installer_url:
            # Release sem instalador: cai para a página da versão.
            try:
                self._open_url(updates.info.url)
            except Exception:
                logger.warning("Falha ao abrir a página da versão", exc_info=True)
            return
        updates.install()

    def _sync_updates(self) -> None:
        """Atualiza a seção conforme o UpdateManager (ouvinte, thread do Tk)."""
        updates = self._updates
        if updates is None or not self.winfo_exists():
            return
        self._update_status.configure(text=update_status_text(updates))
        busy = updates.busy
        self._check_btn.configure(state="disabled" if busy else "normal")
        info = updates.info
        show_install = info is not None and updates.state in (
            UpdateState.AVAILABLE,
            UpdateState.DOWNLOADING,
            UpdateState.ERROR,
        )
        if show_install and info is not None:
            label = f"Atualizar para {info.version}" if info.installer_url else "Abrir página"
            self._install_btn.configure(text=label, state="disabled" if busy else "normal")
            if not self._install_btn.winfo_manager():
                self._install_btn.pack(side="left")
        elif self._install_btn.winfo_manager():
            self._install_btn.pack_forget()

    # ---- tema -------------------------------------------------------------

    def _add_label(self, frame: ctk.CTkFrame, text: str, row: int) -> None:
        label = ctk.CTkLabel(frame, text=text, anchor="w")
        label.grid(row=row, column=0, sticky="w", pady=4)
        self._labels.append(label)

    def _on_theme_selected(self, label: str) -> None:
        key = theme_key_from_label(label)
        if key is None:
            return
        self._apply_palette(get_palette(key))

    def _apply_palette(self, p: Palette) -> None:
        self._palette = p
        apply_window(self, p, "CTkToplevel")
        apply_card(self._frame, p)
        for label in self._labels:
            apply_text(label, p)
        self._message.configure(text_color=p.error)
        for entry in self._entries.values():
            apply_entry(entry, p)
        apply_slider(self._volume, p)
        apply_option_menu(self._theme_menu, p)
        for box in self._checkboxes:
            apply_checkbox(box, p)
        if self._updates is not None:
            for label in (self._updates_title, self._version_label, self._update_status):
                apply_text(label, p)
            apply_accent_button(self._check_btn, p)
            apply_accent_button(self._install_btn, p)
        apply_accent_button(self._cancel_btn, p)
        apply_accent_button(self._save_btn, p)
        refresh_transparent_bg(self)

    # ---- coleta e salvamento ----------------------------------------------

    def collect(self) -> dict[str, object]:
        raw: dict[str, object] = {name: entry.get() for name, entry in self._entries.items()}
        raw["brown_noise_volume"] = self._volume.get()
        for name, var in self._bools.items():
            raw[name] = var.get()
        raw["theme"] = theme_key_from_label(self._theme_menu.get()) or ""
        return raw

    def _save_clicked(self) -> None:
        try:
            new = build_config(self.collect(), self._base)
        except SettingsError as exc:
            self._message.configure(text=str(exc))
            return
        try:
            self._on_save(new)
        except OSError as exc:
            self._message.configure(text=f"Não foi possível salvar: {exc}")
            return
        self.destroy()
