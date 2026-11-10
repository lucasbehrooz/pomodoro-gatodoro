"""Testes do gato animado.

A maior parte é lógica pura (sem janela). O teste de widget Tk só roda com:

    POMODORO_UI_SMOKE=1 pytest tests/test_cat.py
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest
from PIL import Image, ImageChops, ImageSequence

from pomodoro.ui import cat as cat_mod
from pomodoro.ui.cat import (
    CAT_ASSET_PATH,
    DISPLAY_SIZE,
    load_frames,
    resolve_asset_path,
    should_animate,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = REPO_ROOT / "tools" / "make_cat_gif.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("make_cat_gif", GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---- asset e gerador -----------------------------------------------------


def test_asset_gif_exists_with_at_least_8_frames():
    assert CAT_ASSET_PATH.is_file(), f"asset ausente: {CAT_ASSET_PATH}"
    with Image.open(CAT_ASSET_PATH) as gif:
        assert gif.n_frames >= 8
        assert gif.size == (240, 240)
        assert gif.info.get("loop") == 0
        assert gif.info.get("duration") == 120


def test_asset_frames_are_animated_not_identical():
    with Image.open(CAT_ASSET_PATH) as gif:
        frames = [f.convert("RGBA") for f in ImageSequence.Iterator(gif)]
    differing = [
        i
        for i in range(1, len(frames))
        if ImageChops.difference(frames[0], frames[i]).getbbox(alpha_only=False)
    ]
    assert differing, "todos os quadros são iguais"


def test_generator_builds_frames_without_touching_repo(tmp_path: Path):
    gen = _load_generator()
    frames = gen.build_frames()
    assert len(frames) >= 8
    assert all(f.mode == "RGBA" and f.size == (240, 240) for f in frames)

    out = gen.save_gif(tmp_path / "gato.gif")
    with Image.open(out) as gif:
        assert gif.n_frames == len(frames)
        assert gif.info.get("loop") == 0


def test_generator_output_path_points_to_assets():
    gen = _load_generator()
    assert gen.OUTPUT_PATH == REPO_ROOT / "assets" / "gato_pao.gif"


# ---- caminho e decisão ----------------------------------------------------


def test_resolve_asset_path_default_is_repo_asset():
    assert resolve_asset_path() == CAT_ASSET_PATH


def test_resolve_asset_path_accepts_explicit_path(tmp_path: Path):
    custom = tmp_path / "x.gif"
    assert resolve_asset_path(custom) == custom
    assert resolve_asset_path(str(custom)) == custom


def test_should_animate_follows_running_state():
    assert should_animate(True) is True
    assert should_animate(False) is False


# ---- carregamento de quadros ------------------------------------------------


def test_load_frames_real_asset_is_resized():
    frames = load_frames(CAT_ASSET_PATH)
    assert len(frames) >= 8
    assert all(f.size == DISPLAY_SIZE and f.mode == "RGBA" for f in frames)


def test_load_frames_missing_file_returns_empty(tmp_path: Path):
    assert load_frames(tmp_path / "nao_existe.gif") == []


def test_load_frames_invalid_file_returns_empty(tmp_path: Path):
    bogus = tmp_path / "bogus.gif"
    bogus.write_bytes(b"isto nao e um gif")
    assert load_frames(bogus) == []


# ---- widget (opt-in) --------------------------------------------------------

smoke = pytest.mark.skipif(
    os.environ.get("POMODORO_UI_SMOKE") != "1",
    reason="smoke test de UI: defina POMODORO_UI_SMOKE=1 para executar",
)


@smoke
def test_cat_widget_animates_only_when_running(tmp_path: Path):
    import customtkinter as ctk

    try:
        root = ctk.CTk()
    except Exception as exc:  # sem display
        pytest.skip(f"sem display: {exc}")
    try:
        widget = cat_mod.CatAnimation(root)
        widget.pack()
        root.update()
        assert widget.frame_count >= 8
        assert widget.is_running is False
        assert widget._after_id is None  # parado: nenhum after pendente

        widget.set_running(True)
        assert widget._after_id is not None
        widget.set_running(True)  # idempotente
        widget.stop()
        assert widget.frame_index == 0
        assert widget._after_id is None

        widget.set_running(False)  # idempotente quando já parado
        assert widget._after_id is None
    finally:
        root.destroy()


@smoke
def test_cat_widget_missing_asset_does_not_raise(tmp_path: Path):
    import customtkinter as ctk

    try:
        root = ctk.CTk()
    except Exception as exc:  # sem display
        pytest.skip(f"sem display: {exc}")
    try:
        widget = cat_mod.CatAnimation(root, asset_path=tmp_path / "nao_existe.gif")
        widget.pack()
        widget.set_running(True)  # sem frames: não agenda nada
        assert widget.frame_count == 0
        assert widget._after_id is None
        widget.set_running(False)
    finally:
        root.destroy()
