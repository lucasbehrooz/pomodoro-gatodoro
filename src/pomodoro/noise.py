"""Gerador de ruído marrom (apenas geração de sinal, sem reprodução de áudio).

Técnica: ruído branco uniforme integrado por um integrador "vazante"
(leaky integrator)::

    y[n] = BROWN_LEAK * y[n-1] + w[n]

A integração do ruído branco produz espectro ~1/f² (ruído marrom). O fator
de vazamento limita o drift DC. Com BROWN_LEAK = 0.999 e fs = 44100 Hz, a
frequência de canto é ~ (1 - a) * fs / (2*pi) ≈ 7 Hz.

O estado do integrador é mantido entre chamadas de ``next_chunk``, então
chunks consecutivos formam um sinal contínuo sem cliques.

Nota: o fator de vazamento foi escolhido para 44100 Hz. Com outra taxa de
amostragem a frequência de canto muda proporcionalmente.
"""

from __future__ import annotations

import numpy as np

# Fator de vazamento do integrador (0 < a < 1). Próximo de 1 = mais grave, mais drift.
BROWN_LEAK: float = 0.999

# Variância do ruído branco uniforme em [-1, 1] é 1/3.
_WHITE_VARIANCE: float = 1.0 / 3.0

# Desvio-padrão alvo da saída, antes de clipar. Com 0.25 o pico típico (~4 sigma) fica perto de 1.
_TARGET_STD: float = 0.25

# Ganho fixo de saída. Calibrado de forma analítica para std ~= _TARGET_STD em regime permanente:
#   std(y) = sqrt(var_w / (1 - a^2))  ->  BROWN_OUTPUT_SCALE = _TARGET_STD / std(y)
BROWN_OUTPUT_SCALE: float = _TARGET_STD / float(
    np.sqrt(_WHITE_VARIANCE / (1.0 - BROWN_LEAK**2))
)

# Tamanho do bloco para a integração vetorizada (matriz triangular fixa).
_BLOCK: int = 64


def _build_tables(leak: float, block: int) -> tuple[np.ndarray, np.ndarray]:
    """Pré-calcula a matriz triangular T[i, j] = a^(i-j) (i >= j) e o vetor a^(i+1)."""
    idx = np.arange(block)
    diff = idx[:, None] - idx[None, :]
    tri = np.where(diff >= 0, leak ** np.clip(diff, 0, None), 0.0)
    decay = leak ** (idx + 1)
    return tri, decay


_TRI, _DECAY = _build_tables(BROWN_LEAK, _BLOCK)


class BrownNoiseGenerator:
    """Gera ruído marrom em chunks contínuos, mantendo o estado do integrador."""

    def __init__(self, sample_rate: int = 44100, seed: int | None = None) -> None:
        if sample_rate <= 0:
            raise ValueError("sample_rate deve ser positivo")
        self.sample_rate = int(sample_rate)
        # Sempre há um seed concreto, para que reset() reproduza o início.
        if seed is None:
            seed = int(np.random.SeedSequence().entropy) % (2**32)
        self._seed = int(seed)
        self._rng = np.random.default_rng(self._seed)
        self._state = 0.0  # último valor do integrador (sem escala)

    def reset(self) -> None:
        """Zera o integrador e reinicia o RNG a partir do seed original."""
        self._rng = np.random.default_rng(self._seed)
        self._state = 0.0

    def next_chunk(self, frames: int) -> np.ndarray:
        """Retorna ``frames`` amostras float32 de ruído marrom em [-1, 1]."""
        if frames < 0:
            raise ValueError("frames não pode ser negativo")
        if frames == 0:
            return np.zeros(0, dtype=np.float32)

        white = self._rng.uniform(-1.0, 1.0, size=frames)
        out = np.empty(frames, dtype=np.float64)
        y_prev = self._state

        for start in range(0, frames, _BLOCK):
            block = white[start : start + _BLOCK]
            r = block.shape[0]
            # y[n] = a^(n+1) * y_prev + sum_{k<=n} a^(n-k) * w[k]
            y_block = _TRI[:r, :r] @ block + _DECAY[:r] * y_prev
            out[start : start + r] = y_block
            y_prev = y_block[-1]

        self._state = float(y_prev)
        scaled = out * BROWN_OUTPUT_SCALE
        return np.clip(scaled, -1.0, 1.0).astype(np.float32)


def apply_gain_ramp(chunk: np.ndarray, start_gain: float, end_gain: float) -> np.ndarray:
    """Aplica um ganho linear de ``start_gain`` a ``end_gain`` sobre o chunk.

    Retorna um novo array float32 com o mesmo shape. Não altera a entrada e
    não tem estado, então serve para fade in/out sem clique.
    """
    x = np.asarray(chunk, dtype=np.float32)
    n = x.shape[-1] if x.ndim else 0
    if n == 0:
        return x.copy()
    gains = np.linspace(start_gain, end_gain, n, dtype=np.float64).astype(np.float32)
    return (x * gains).astype(np.float32)
