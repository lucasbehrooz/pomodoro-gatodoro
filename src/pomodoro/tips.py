"""Dicas mostradas na notificação de início de pausa.

Sem dependência de interface. ``pick_tip`` recebe o gerador aleatório
(``random.Random`` ou compatível) para que os testes sejam determinísticos.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from typing import Optional

TIPS: tuple[str, ...] = (
    "Beba água",
    "Alongue o pescoço e os ombros",
    "Olhe para longe da tela por 20 segundos",
    "Levante e caminhe um pouco",
    "Respire fundo 3 vezes",
    "Alongue os braços e os punhos",
    "Pisque devagar algumas vezes para descansar os olhos",
    "Ajuste a postura: costas apoiadas e ombros soltos",
    "Abra a janela ou pegue um pouco de ar fresco",
    "Arrume a mesa por um minuto",
)


def pick_tip(
    rng: random.Random,
    previous: Optional[str] = None,
    tips: Sequence[str] = TIPS,
) -> str:
    """Escolhe uma dica aleatória, diferente de ``previous`` quando possível."""
    if not tips:
        raise ValueError("lista de dicas vazia")
    options = [tip for tip in tips if tip != previous] or list(tips)
    return rng.choice(options)


def with_tip(message: str, tip: str) -> str:
    """Junta a mensagem da notificação e a dica: 'Hora da pausa. Dica: Beba água.'"""
    return f"{message}. Dica: {tip}."
