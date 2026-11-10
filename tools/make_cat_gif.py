"""Gera assets/gato_pao.gif: um gato estilizado amassando pão, desenhado com Pillow.

Uso (na raiz do repositório):

    python tools/make_cat_gif.py

Desenho em canvas 480x480 (coordenadas de desenho) e reduzido para 240x240
com LANCZOS, para bordas suaves. Fundo transparente, RGBA, disposal=2 (cada
quadro substitui o anterior), loop infinito, 120 ms por quadro. Depende
apenas de Pillow.

Para trocar por um GIF real, basta sobrescrever assets/gato_pao.gif.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

FINAL_SIZE = 240
CANVAS = 480  # coordenadas de desenho; a saída é reduzida para FINAL_SIZE
FRAME_COUNT = 10
FRAME_MS = 120

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "assets" / "gato_pao.gif"

# Paleta
BODY = (238, 146, 58, 255)
BODY_SHADE = (214, 118, 40, 255)
OUTLINE = (110, 56, 22, 255)
INNER_EAR = (255, 170, 170, 255)
EYE = (60, 36, 20, 255)
NOSE = (235, 110, 120, 255)
BLUSH = (255, 110, 120, 110)
DOUGH = (246, 214, 150, 255)
DOUGH_SHADE = (214, 170, 100, 255)
FLOUR = (255, 252, 240, 255)


def _w(final_px: float) -> int:
    """Espessura de traço em pixels do GIF final (2x no canvas de desenho)."""
    return max(1, round(final_px * 2))


def _box(x0: float, y0: float, x1: float, y1: float) -> tuple[int, int, int, int]:
    return (round(x0), round(y0), round(x1), round(y1))


def _pt(x: float, y: float) -> tuple[int, int]:
    return (round(x), round(y))


def _draw_tail(draw: ImageDraw.ImageDraw, wag: float) -> None:
    # Cauda curva saindo do lado direito do corpo, balançando levemente.
    points = [
        _pt(318, 318),
        _pt(352, 300 + 6 * wag),
        _pt(366, 262 + 10 * wag),
        _pt(354, 232 + 8 * wag),
    ]
    draw.line(points, fill=OUTLINE, width=_w(11))
    draw.line(points, fill=BODY, width=_w(7))


def _draw_dough(draw: ImageDraw.ImageDraw, squash: float) -> None:
    # Massa redonda; "achata" um pouco quando as patas estão pressionando.
    top = 300 + 6 * squash
    draw.ellipse(_box(96, top, 384, 404), fill=DOUGH, outline=DOUGH_SHADE, width=_w(1.5))
    draw.ellipse(_box(130, top + 10, 220, top + 36), fill=(255, 236, 190, 255))


def _draw_paw(draw: ImageDraw.ImageDraw, x: float, y: float) -> None:
    draw.rounded_rectangle(
        _box(x, y, x + 62, y + 46),
        radius=22,
        fill=BODY,
        outline=OUTLINE,
        width=_w(1.5),
    )
    # Dedinhos
    for dx in (14, 31, 48):
        draw.line([_pt(x + dx, y + 30), _pt(x + dx, y + 40)], fill=OUTLINE, width=_w(1))


def _draw_flour(draw: ImageDraw.ImageDraw, frame: int) -> None:
    # Farinha que espirra quando as patas afundam na massa.
    spots = [(150, 372), (300, 380), (226, 392), (176, 396), (286, 352)]
    for k, (x, y) in enumerate(spots):
        if (frame + k) % 3 == 0:
            draw.ellipse(_box(x - 3, y - 3, x + 3, y + 3), fill=FLOUR)


def draw_frame(index: int, total: int = FRAME_COUNT) -> Image.Image:
    """Desenha o quadro `index` (0-based) em RGBA FINAL_SIZE x FINAL_SIZE."""
    phase = 2 * math.pi * index / total
    img = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Patas alternam: uma sobe enquanto a outra desce.
    lift_left = 14 * (1 + math.sin(phase)) / 2  # 0..14 unidades de desenho
    lift_right = 14 * (1 + math.sin(phase + math.pi)) / 2
    squash = (math.sin(phase + math.pi) + 1) / 2
    wag = math.sin(phase)

    _draw_tail(draw, wag)
    _draw_dough(draw, squash)

    # Corpo (oval) e pernas traseiras.
    draw.ellipse(_box(146, 196, 334, 356), fill=BODY, outline=OUTLINE, width=_w(2))
    draw.ellipse(_box(158, 320, 196, 352), fill=BODY_SHADE, outline=OUTLINE, width=_w(1.5))
    draw.ellipse(_box(284, 320, 322, 352), fill=BODY_SHADE, outline=OUTLINE, width=_w(1.5))

    # Orelhas (atrás da cabeça).
    draw.polygon([_pt(184, 122), _pt(190, 52), _pt(236, 102)], fill=BODY, outline=OUTLINE)
    draw.polygon([_pt(296, 122), _pt(290, 52), _pt(244, 102)], fill=BODY, outline=OUTLINE)
    draw.polygon([_pt(196, 110), _pt(198, 68), _pt(225, 100)], fill=INNER_EAR)
    draw.polygon([_pt(284, 110), _pt(282, 68), _pt(255, 100)], fill=INNER_EAR)

    # Cabeça.
    draw.ellipse(_box(168, 88, 312, 232), fill=BODY, outline=OUTLINE, width=_w(2))

    # Olhos felizes fechados ("^ ^").
    draw.arc(_box(192, 136, 222, 166), start=200, end=340, fill=EYE, width=_w(2.5))
    draw.arc(_box(258, 136, 288, 166), start=200, end=340, fill=EYE, width=_w(2.5))

    # Bochechas (com alfa, por isso compostas em uma camada própria).
    blush = Image.new("RGBA", img.size, (0, 0, 0, 0))
    blush_draw = ImageDraw.Draw(blush)
    blush_draw.ellipse(_box(176, 172, 200, 188), fill=BLUSH)
    blush_draw.ellipse(_box(280, 172, 304, 188), fill=BLUSH)
    img.alpha_composite(blush)
    draw = ImageDraw.Draw(img)

    # Focinho e boca.
    draw.ellipse(_box(230, 176, 250, 188), fill=NOSE)
    draw.arc(_box(224, 180, 240, 200), start=0, end=120, fill=EYE, width=_w(1.5))
    draw.arc(_box(240, 180, 256, 200), start=60, end=180, fill=EYE, width=_w(1.5))

    # Patas da frente, sobre a massa.
    _draw_paw(draw, 164, 330 - lift_left)
    _draw_paw(draw, 254, 330 - lift_right)

    _draw_flour(draw, index)

    return img.resize((FINAL_SIZE, FINAL_SIZE), Image.Resampling.LANCZOS)


def build_frames(total: int = FRAME_COUNT) -> list[Image.Image]:
    return [draw_frame(i, total) for i in range(total)]


def save_gif(path: Path = OUTPUT_PATH, total: int = FRAME_COUNT) -> Path:
    frames = build_frames(total)
    path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_MS,
        loop=0,
        disposal=2,
    )
    return path


def main() -> None:
    path = save_gif()
    print(f"GIF gerado: {path} ({FRAME_COUNT} quadros, {FRAME_MS} ms, {FINAL_SIZE}x{FINAL_SIZE})")


if __name__ == "__main__":
    main()
