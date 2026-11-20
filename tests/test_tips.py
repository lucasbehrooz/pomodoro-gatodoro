"""Testes das dicas de pausa (sem display)."""

from __future__ import annotations

import random

import pytest

from pomodoro.tips import TIPS, pick_tip, with_tip


def test_tips_list_is_in_portuguese_and_unique():
    assert len(TIPS) >= 10
    assert len(set(TIPS)) == len(TIPS)
    assert "Beba água" in TIPS
    assert all(tip and tip == tip.strip() and not tip.endswith(".") for tip in TIPS)


def test_pick_tip_returns_a_tip_from_the_list():
    rng = random.Random(1)
    for _ in range(50):
        assert pick_tip(rng) in TIPS


def test_pick_tip_is_deterministic_with_injected_rng():
    a = [pick_tip(random.Random(42)) for _ in range(3)]
    b = [pick_tip(random.Random(42)) for _ in range(3)]
    assert a == b
    seq1, seq2 = random.Random(7), random.Random(7)
    assert [pick_tip(seq1) for _ in range(10)] == [pick_tip(seq2) for _ in range(10)]


def test_pick_tip_never_repeats_previous():
    rng = random.Random(0)
    previous = None
    for _ in range(200):
        tip = pick_tip(rng, previous)
        assert tip != previous
        previous = tip


def test_pick_tip_with_single_tip_repeats_it():
    assert pick_tip(random.Random(0), "Beba água", tips=["Beba água"]) == "Beba água"


def test_pick_tip_empty_list_fails():
    with pytest.raises(ValueError):
        pick_tip(random.Random(0), tips=[])


def test_with_tip_format():
    assert with_tip("Hora da pausa", "Beba água") == "Hora da pausa. Dica: Beba água."
