"""Gato animado (amassando pão) exibido enquanto o timer executa.

Threading: todos os métodos devem rodar na thread do Tk. A animação é
dirigida por ``self.after``; quando parada não há nenhum agendamento pendente,
então não consome CPU.

As funções de módulo (``resolve_asset_path``, ``should_animate``,
``load_frames``) não dependem de janela e são testáveis sem display.
"""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageSequence, UnidentifiedImageError

from pomodoro.assets import CAT_GIF_PATH as CAT_ASSET_PATH

DISPLAY_SIZE: tuple[int, int] = (150, 150)
FRAME_MS = 120
FALLBACK_TEXT = "(gato indisponível)"


def resolve_asset_path(path: Path | str | None = None) -> Path:
    """Caminho do GIF do gato. Sem argumento, usa o asset do repositório."""
    return Path(path) if path is not None else CAT_ASSET_PATH


def should_animate(is_running: bool) -> bool:
    """Decide se o gato deve animar: só enquanto o timer está executando."""
    return bool(is_running)


def load_frames(path: Path | str, size: tuple[int, int] = DISPLAY_SIZE) -> list[Image.Image]:
    """Carrega os quadros do GIF como RGBA redimensionados para ``size``.

    Retorna lista vazia se o arquivo não existir ou não for um GIF legível;
    nunca levanta exceção por causa do asset.
    """
    try:
        with Image.open(path) as gif:
            frames = [
                frame.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
                for frame in ImageSequence.Iterator(gif)
            ]
    except (OSError, UnidentifiedImageError, ValueError):
        return []
    return frames


class CatAnimation(ctk.CTkFrame):
    """Mostra o gato animado. Anima somente com ``start()``/``set_running(True)``."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        asset_path: Path | str | None = None,
        size: tuple[int, int] = DISPLAY_SIZE,
        frame_ms: int = FRAME_MS,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._frame_ms = frame_ms
        self._images: list[ctk.CTkImage] = [
            ctk.CTkImage(light_image=frame, dark_image=frame, size=size)
            for frame in load_frames(resolve_asset_path(asset_path), size)
        ]
        self._index = 0
        self._running = False
        self._after_id: str | None = None

        if self._images:
            self._label = ctk.CTkLabel(self, text="", image=self._images[0])
        else:
            self._label = ctk.CTkLabel(self, text=FALLBACK_TEXT)
        self._label.pack()

    # ---- estado ----------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def frame_index(self) -> int:
        return self._index

    @property
    def frame_count(self) -> int:
        return len(self._images)

    # ---- controle --------------------------------------------------------

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        if self._images and self._after_id is None:
            self._schedule()

    def stop(self) -> None:
        """Para a animação e congela no primeiro quadro."""
        if not self._running:
            return
        self._running = False
        self._cancel()
        self._show(0)

    def set_running(self, running: bool) -> None:
        """Anima somente quando ``running`` é True. Idempotente, seguro a cada tick."""
        if should_animate(running):
            self.start()
        else:
            self.stop()

    def destroy(self) -> None:
        self._running = False
        self._cancel()
        super().destroy()

    # ---- internos --------------------------------------------------------

    def _schedule(self) -> None:
        self._after_id = self.after(self._frame_ms, self._advance)

    def _cancel(self) -> None:
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except Exception:  # pragma: no cover - Tk já destruído
                pass
            self._after_id = None

    def _advance(self) -> None:
        self._after_id = None
        if not self._running or not self._images:
            return
        self._show((self._index + 1) % len(self._images))
        self._schedule()

    def _show(self, index: int) -> None:
        self._index = index
        if self._images:
            self._label.configure(image=self._images[index])
