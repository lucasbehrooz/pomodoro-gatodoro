"""Diálogo de configurações (CTkToplevel). Valida via settings.build_config."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from pomodoro.config import Config
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
    ) -> None:
        super().__init__(master)
        self.title("Configurações")
        self.resizable(False, False)
        self.transient(master)

        self._base = config
        self._on_save = on_save
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
