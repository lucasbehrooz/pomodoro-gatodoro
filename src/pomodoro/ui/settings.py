"""Conversão e validação dos campos do formulário de configurações. Sem widgets."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from pomodoro.config import DAILY_GOAL_RANGE, PRE_END_WARNING_RANGE, Config
from pomodoro.noise import NOISE_COLORS
from pomodoro.ui.theme import THEMES

# Faixas válidas para os campos inteiros do formulário (inclusive).
INT_FIELDS: dict[str, tuple[int, int]] = {
    "focus_minutes": (1, 180),
    "short_break_minutes": (1, 60),
    "long_break_minutes": (1, 120),
    "cycles_before_long_break": (1, 12),
    "daily_goal": DAILY_GOAL_RANGE,
    "pre_end_warning_seconds": PRE_END_WARNING_RANGE,
}

BOOL_FIELDS: tuple[str, ...] = (
    "sound_enabled",
    "toast_enabled",
    "brown_noise_enabled",
    "brown_noise_focus_only",
    "close_to_tray",
    "start_with_windows",
    "check_updates",
    "auto_start_breaks",
    "auto_start_focus",
    "show_task_field",
    "compact_mode",
)

CHOICE_FIELDS: dict[str, list[str]] = {
    "noise_color": list(NOISE_COLORS.keys()),
}

LABELS: dict[str, str] = {
    "focus_minutes": "Duração do foco (min)",
    "short_break_minutes": "Pausa curta (min)",
    "long_break_minutes": "Pausa longa (min)",
    "cycles_before_long_break": "Focos até a pausa longa",
    "daily_goal": "Meta diária de focos (0 = sem meta)",
    "brown_noise_volume": "Volume do ruído (%)",
    "sound_enabled": "Som de alerta",
    "toast_enabled": "Notificação do Windows",
    "brown_noise_enabled": "Ruído marrom",
    "brown_noise_focus_only": "Ruído só durante o foco",
    "close_to_tray": "Fechar a janela manda para a bandeja",
    "start_with_windows": "Iniciar com o Windows",
    "check_updates": "Avisar quando houver nova versão",
    "theme": "Tema",
    "auto_start_breaks": "Iniciar pausas automaticamente",
    "auto_start_focus": "Iniciar focos automaticamente",
    "pre_end_warning_seconds": "Aviso antes do fim do foco (s, 0 = desligado)",
    "show_task_field": "Mostrar campo de tarefa na tela inicial",
    "compact_mode": "Modo compacto (janela pequena sempre no topo)",
    "noise_color": "Cor do ruído de fundo",
}


class SettingsError(ValueError):
    """Valor inválido em um campo do formulário. A mensagem é exibível ao usuário."""


def form_values(config: Config) -> dict[str, object]:
    """Valores iniciais do formulário a partir da configuração.

    O volume é apresentado em porcentagem (0 a 100); a Config guarda 0.0 a 1.0.
    """
    values: dict[str, object] = {name: getattr(config, name) for name in INT_FIELDS}
    values["brown_noise_volume"] = round(config.brown_noise_volume * 100, 1)
    for name in BOOL_FIELDS:
        values[name] = getattr(config, name)
    values["theme"] = config.theme
    return values


def _parse_int(raw: object, name: str) -> int:
    label = LABELS[name]
    try:
        value = int(str(raw).strip())
    except ValueError:
        raise SettingsError(f"{label}: informe um número inteiro.") from None
    lo, hi = INT_FIELDS[name]
    if not lo <= value <= hi:
        raise SettingsError(f"{label}: informe um valor entre {lo} e {hi}.")
    return value


def _parse_volume_percent(raw: object) -> float:
    label = LABELS["brown_noise_volume"]
    try:
        percent = float(str(raw).strip().replace(",", "."))
    except ValueError:
        raise SettingsError(f"{label}: informe um número.") from None
    if not 0 <= percent <= 100:
        raise SettingsError(f"{label}: informe um valor entre 0 e 100.")
    return round(percent / 100, 3)


def build_config(raw: Mapping[str, object], base: Config) -> Config:
    """Monta uma Config nova a partir dos valores do formulário.

    Campos não presentes em ``raw`` mantêm o valor de ``base``. Lança
    SettingsError com mensagem em português se algum valor for inválido.
    """
    updates: dict[str, object] = {}
    for name in INT_FIELDS:
        if name in raw:
            updates[name] = _parse_int(raw[name], name)
    if "brown_noise_volume" in raw:
        updates["brown_noise_volume"] = _parse_volume_percent(raw["brown_noise_volume"])
    for name in BOOL_FIELDS:
        if name in raw:
            updates[name] = bool(raw[name])
    if "theme" in raw:
        theme = raw["theme"]
        if not isinstance(theme, str) or theme not in THEMES:
            raise SettingsError(f"{LABELS['theme']}: escolha uma opção válida.")
        updates["theme"] = theme
    return replace(base, **updates)
