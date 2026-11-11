"""Caminhos dos assets (GIF do gato, ícones).

Funciona no repositório e dentro do executável do PyInstaller (sys._MEIPASS).
"""

from __future__ import annotations

import sys
from pathlib import Path


def asset_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    # src/pomodoro/assets.py -> parents[2] é a raiz do repositório.
    return Path(__file__).resolve().parents[2]


ASSETS_DIR = asset_root() / "assets"
CAT_GIF_PATH = ASSETS_DIR / "gato_pao.gif"
ICON_ICO_PATH = ASSETS_DIR / "gato.ico"
ICON_PNG_PATH = ASSETS_DIR / "gato.png"
