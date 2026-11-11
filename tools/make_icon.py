"""Gera o ícone do app a partir do gato desenhado em tools/make_cat_gif.py.

Uso (na raiz do repositório):

    python tools/make_icon.py

Saídas:
    assets/gato.ico  - ícone do .exe e da janela (vários tamanhos)
    assets/gato.png  - ícone da bandeja (64x64)
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_cat_gif import draw_frame  # noqa: E402

ASSETS = Path(__file__).resolve().parents[1] / "assets"
ICO_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def build_icon_source() -> Image.Image:
    """Quadro do gato recortado ao conteúdo e centralizado em quadrado transparente."""
    frame = draw_frame(0).convert("RGBA")
    box = frame.getbbox()
    cropped = frame.crop(box) if box else frame
    side = max(cropped.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(cropped, ((side - cropped.width) // 2, (side - cropped.height) // 2))
    return square.resize((256, 256), Image.LANCZOS)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    source = build_icon_source()
    source.save(ASSETS / "gato.ico", format="ICO", sizes=ICO_SIZES)
    source.resize((64, 64), Image.LANCZOS).save(ASSETS / "gato.png")
    print(f"Gerado: {ASSETS / 'gato.ico'} e {ASSETS / 'gato.png'}")


if __name__ == "__main__":
    main()
