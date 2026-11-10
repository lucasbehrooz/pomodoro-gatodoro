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


class SettingsDialog(ctk.CTkToplevel):
    """Coleta os valores e chama on_save(new_config).

    on_save persiste e aplica a configuração (ex.: save_config + apply_config).
    Pode lançar OSError (falha ao salvar), que é mostrada no diálogo sem fechá-lo.
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
        values = form_values(config)

        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        self._entries: dict[str, ctk.CTkEntry] = {}
        row = 0
        for name in INT_FIELDS:
            ctk.CTkLabel(frame, text=LABELS[name], anchor="w").grid(
                row=row, column=0, sticky="w", pady=4
            )
            entry = ctk.CTkEntry(frame, width=80)
            entry.insert(0, str(values[name]))
            entry.grid(row=row, column=1, sticky="e", pady=4)
            self._entries[name] = entry
            row += 1

        ctk.CTkLabel(frame, text=LABELS["brown_noise_volume"], anchor="w").grid(
            row=row, column=0, sticky="w", pady=4
        )
        self._volume = ctk.CTkSlider(frame, from_=0, to=100, number_of_steps=100, width=160)
        self._volume.set(float(values["brown_noise_volume"]))  # type: ignore[arg-type]
        self._volume.grid(row=row, column=1, sticky="e", pady=4)
        row += 1

        self._bools: dict[str, ctk.BooleanVar] = {}
        for name in BOOL_FIELDS:
            var = ctk.BooleanVar(value=bool(values[name]))
            ctk.CTkCheckBox(frame, text=LABELS[name], variable=var).grid(
                row=row, column=0, columnspan=2, sticky="w", pady=2
            )
            self._bools[name] = var
            row += 1

        self._message = ctk.CTkLabel(frame, text="", text_color="#d9534f", wraplength=320)
        self._message.grid(row=row, column=0, columnspan=2, sticky="w", pady=(8, 0))
        row += 1

        buttons = ctk.CTkFrame(frame, fg_color="transparent")
        buttons.grid(row=row, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ctk.CTkButton(buttons, text="Cancelar", width=90, command=self.destroy).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(buttons, text="Salvar", width=90, command=self._save_clicked).pack(
            side="left"
        )

    def collect(self) -> dict[str, object]:
        raw: dict[str, object] = {name: entry.get() for name, entry in self._entries.items()}
        raw["brown_noise_volume"] = self._volume.get()
        for name, var in self._bools.items():
            raw[name] = var.get()
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
