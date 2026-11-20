"""Configuração do app: dataclass + load/save em JSON (%APPDATA%\\Pomodoro\\config.json)."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path

from pomodoro.ui.theme import DEFAULT_THEME, is_valid_theme

# Faixa válida (inclusive) do aviso antes do fim do foco, em segundos.
PRE_END_WARNING_RANGE: tuple[int, int] = (0, 300)


@dataclass
class Config:
    # Durações em minutos
    focus_minutes: int = 25
    short_break_minutes: int = 5
    long_break_minutes: int = 15
    # Quantos focos até a pausa longa
    cycles_before_long_break: int = 4

    # Notificações
    sound_enabled: bool = True
    toast_enabled: bool = True

    # Ruído marrom
    brown_noise_enabled: bool = False
    # Padrão decidido: True = toca só no foco; False = toca também nas pausas
    brown_noise_focus_only: bool = True
    brown_noise_volume: float = 0.3  # 0.0 a 1.0

    # Janela
    close_to_tray: bool = True

    # Sistema: abrir junto com o Windows (ver pomodoro.autostart)
    start_with_windows: bool = False
    # Tema visual: "padrao", "feminino" ou "escuro" (ver pomodoro.ui.theme)
    theme: str = DEFAULT_THEME

    # Atualizações: avisar quando houver versão nova (ver pomodoro.updater)
    check_updates: bool = True
    # Versão que o usuário pediu para não ser avisado de novo (ex.: "0.0.8")
    skipped_version: str = ""

    # Aviso antes do fim do foco: som curto quando faltar este tempo (segundos).
    # 0 desliga. Faixa válida: PRE_END_WARNING_RANGE.
    pre_end_warning_seconds: int = 60


def config_dir() -> Path:
    """Diretório de dados do app. Em Windows usa %APPDATA%; fora dele, ~/.config."""
    base = os.environ.get("APPDATA")
    root = Path(base) if base else Path.home() / ".config"
    return root / "Pomodoro"


def config_path() -> Path:
    return config_dir() / "config.json"


def load_config(path: Path | None = None) -> Config:
    """Carrega a configuração. Arquivo ausente ou corrompido resulta nos padrões.

    Chaves desconhecidas são ignoradas; chaves ausentes usam o padrão.
    """
    path = path or config_path()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return Config()
    if not isinstance(raw, dict):
        return Config()

    known = {f.name for f in fields(Config)}
    config = Config(**{k: v for k, v in raw.items() if k in known})
    if not is_valid_theme(config.theme):
        config = replace(config, theme=DEFAULT_THEME)
    if not isinstance(config.start_with_windows, bool):
        config = replace(config, start_with_windows=False)
    if not isinstance(config.check_updates, bool):
        config = replace(config, check_updates=True)
    if not isinstance(config.skipped_version, str):
        config = replace(config, skipped_version="")
    if not _valid_pre_end_warning(config.pre_end_warning_seconds):
        config = replace(config, pre_end_warning_seconds=Config.pre_end_warning_seconds)
    return config


def _valid_pre_end_warning(value: object) -> bool:
    lo, hi = PRE_END_WARNING_RANGE
    return isinstance(value, int) and not isinstance(value, bool) and lo <= value <= hi


def save_config(config: Config, path: Path | None = None) -> None:
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(config), indent=2, ensure_ascii=False), encoding="utf-8")
