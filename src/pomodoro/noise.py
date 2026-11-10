"""Gerador de ruído marrom e player de reprodução (sounddevice, importado sob demanda).

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

import logging
import math
import threading
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

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


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------

_CHANNELS: int = 2  # saída estéreo; o mono do gerador é duplicado nos dois canais
_VOLUME_RAMP_SECONDS: float = 0.02  # suavização de set_volume
_PAUSE_FADE_SECONDS: float = 0.02  # fade rápido ao silenciar/retomar em pause_for_alert
_STOP_WAIT_MARGIN: float = 0.5  # tolerância extra para o fade do stop()


def _clamp_unit(v: float) -> float:
    value = float(v)
    if not math.isfinite(value):
        raise ValueError("volume deve ser um número finito")
    return min(max(value, 0.0), 1.0)


def _rate_per_frame(seconds: float, sample_rate: int) -> float:
    """Variação máxima por amostra para ir de 0 a 1 em ``seconds`` (inf = instantâneo)."""
    if seconds <= 0:
        return math.inf
    return 1.0 / (seconds * sample_rate)


def _ramp_block(
    current: float, target: float, rate: float, n: int
) -> tuple[np.ndarray, float]:
    """Valores por amostra indo de ``current`` a ``target`` à taxa ``rate`` (por amostra).

    A taxa é fixa durante toda a transição (é definida uma vez, não por bloco),
    então a rampa é linear e termina exatamente em ``target``.
    Retorna (valores de tamanho n, novo estado).
    """
    if n <= 0:
        return np.zeros(0, dtype=np.float64), current
    if current == target or math.isinf(rate):
        return np.full(n, target, dtype=np.float64), target
    direction = 1.0 if target > current else -1.0
    vals = current + direction * rate * np.arange(1, n + 1, dtype=np.float64)
    vals = np.clip(vals, min(current, target), max(current, target))
    return vals, float(vals[-1])


class BrownNoisePlayer:
    """Reproduz ruído marrom em loop via ``sounddevice.OutputStream`` (modo callback).

    - ``start``/``stop`` com fade in/out sem clique. ``stop`` bloqueia no máximo
      ``fade_seconds + 0.5`` s enquanto o fade roda na callback.
    - ``set_volume`` é suavizado.
    - ``pause_for_alert`` silencia por N segundos e retoma sozinho, medido em
      frames processados pela callback (sem sleep).
    - Se o áudio não estiver disponível, ``start`` registra o erro, não levanta
      exceção e deixa ``is_playing`` False e ``is_available`` False.

    Métodos públicos são seguros para chamar a partir de outra thread (ex.: Tk).
    """

    def __init__(
        self, sample_rate: int = 44100, volume: float = 0.3, block_frames: int = 1024
    ) -> None:
        if sample_rate <= 0:
            raise ValueError("sample_rate deve ser positivo")
        if block_frames <= 0:
            raise ValueError("block_frames deve ser positivo")
        self.sample_rate = int(sample_rate)
        self.block_frames = int(block_frames)
        self._gen = BrownNoiseGenerator(sample_rate=self.sample_rate)

        # _ctl_lock serializa start/stop/close. _state_lock protege o estado lido
        # pela callback; a callback nunca toma _ctl_lock (evita deadlock).
        self._ctl_lock = threading.RLock()
        self._state_lock = threading.Lock()
        self._fade_done = threading.Event()

        self._stream: Any = None
        self._available = True
        self._intent = False  # True enquanto deve estar tocando
        self._volume = _clamp_unit(volume)
        self._vol_cur = self._volume  # volume efetivo (suavizado), usado pela callback
        self._env = 0.0  # envelope atual (fade/pausa), usado pela callback
        self._env_target = 0.0
        self._env_rate = math.inf  # taxa por amostra da transição atual
        self._pause_until: int | None = None  # em frames processados
        self._frames_played = 0
        self._callbacks_seen = 0

    # -- propriedades -------------------------------------------------------

    @property
    def is_playing(self) -> bool:
        with self._state_lock:
            return bool(self._intent and self._stream is not None)

    @property
    def is_available(self) -> bool:
        """False após uma tentativa de start que falhou (sem dispositivo, sem sounddevice)."""
        with self._state_lock:
            return self._available

    # -- controle -----------------------------------------------------------

    def start(self, fade_seconds: float = 0.5) -> None:
        """Inicia a reprodução com fade in. No-op se já estiver tocando."""
        fade = max(0.0, float(fade_seconds))
        with self._ctl_lock:
            with self._state_lock:
                if self._intent:
                    return
                if self._stream is not None:
                    # Um stop() com fade está em andamento: cancela o fade-out.
                    self._intent = True
                    self._pause_until = None
                    self._set_envelope(1.0, fade)
                    self._fade_done.set()
                    return

            try:
                stream = self._open_stream()
            except Exception as exc:  # sounddevice ausente (OSError/ImportError) ou sem dispositivo
                logger.warning("Áudio indisponível; ruído marrom desativado: %s", exc)
                with self._state_lock:
                    self._available = False
                return

            with self._state_lock:
                self._stream = stream
                self._intent = True
                self._available = True
                self._pause_until = None
                self._env = 0.0
                self._set_envelope(1.0, fade)
                self._callbacks_seen = 0
                self._fade_done.clear()

            try:
                stream.start()
            except Exception as exc:
                logger.warning("Falha ao iniciar a reprodução de áudio: %s", exc)
                with self._state_lock:
                    self._stream = None
                    self._intent = False
                    self._available = False
                self._close_stream(stream)

    def stop(self, fade_seconds: float = 0.5) -> None:
        """Faz fade out e fecha o stream. Retorna após o fade (limitado a fade + 0.5 s)."""
        fade = max(0.0, float(fade_seconds))
        with self._ctl_lock:
            with self._state_lock:
                if self._stream is None:
                    self._intent = False
                    return
                was_playing = self._intent
                self._intent = False
                self._pause_until = None
                if fade > 0 and self._callbacks_seen > 0:
                    if was_playing:
                        self._fade_done.clear()
                    self._set_envelope(0.0, fade)
                    wait = True
                else:
                    self._env = 0.0
                    self._set_envelope(0.0, 0.0)
                    wait = False
                done = self._fade_done

        if wait:
            done.wait(fade + _STOP_WAIT_MARGIN)

        with self._ctl_lock:
            with self._state_lock:
                if self._intent or self._stream is None:
                    # start() cancelou o stop, ou close() já fechou o stream.
                    return
                stream = self._stream
                self._stream = None
                self._env = 0.0
            self._close_stream(stream)

    def set_volume(self, v: float) -> None:
        """Define o volume em [0, 1] (valores fora são limitados). Aplicado com suavização."""
        value = _clamp_unit(v)
        with self._state_lock:
            self._volume = value

    def pause_for_alert(self, seconds: float = 3.0) -> None:
        """Silencia por ``seconds`` e retoma automaticamente. No-op se não estiver tocando."""
        duration = max(0.0, float(seconds))
        with self._state_lock:
            if not self._intent or duration <= 0:
                return
            self._pause_until = self._frames_played + int(round(duration * self.sample_rate))
            self._set_envelope(0.0, _PAUSE_FADE_SECONDS)

    def close(self) -> None:
        """Para o stream e libera recursos. Idempotente."""
        with self._ctl_lock:
            with self._state_lock:
                stream = self._stream
                self._stream = None
                self._intent = False
                self._pause_until = None
                self._env = 0.0
                self._set_envelope(0.0, 0.0)
                self._fade_done.set()
            if stream is not None:
                self._close_stream(stream)

    # -- internos -----------------------------------------------------------

    def _set_envelope(self, target: float, seconds: float) -> None:
        # Deve ser chamado com _state_lock adquirido.
        self._env_target = target
        self._env_rate = _rate_per_frame(seconds, self.sample_rate)

    def _open_stream(self) -> Any:
        # Import lazy: sounddevice exige PortAudio e falha ao ser importado sem ele.
        import sounddevice as sd

        return sd.OutputStream(
            samplerate=self.sample_rate,
            blocksize=self.block_frames,
            channels=_CHANNELS,
            dtype="float32",
            callback=self._callback,
        )

    @staticmethod
    def _close_stream(stream: Any) -> None:
        try:
            stream.stop()
        except Exception:  # stream pode não estar ativo
            logger.debug("stream.stop() falhou", exc_info=True)
        try:
            stream.close()
        except Exception:
            logger.debug("stream.close() falhou", exc_info=True)

    def _callback(self, outdata: Any, frames: int, time_info: Any, status: Any) -> None:
        n = int(frames)
        sr = self.sample_rate
        with self._state_lock:
            self._callbacks_seen += 1
            if self._pause_until is not None and self._frames_played >= self._pause_until:
                self._pause_until = None
                if self._intent:
                    self._set_envelope(1.0, _PAUSE_FADE_SECONDS)
            env, self._env = _ramp_block(self._env, self._env_target, self._env_rate, n)
            vol, self._vol_cur = _ramp_block(
                self._vol_cur, self._volume, _rate_per_frame(_VOLUME_RAMP_SECONDS, sr), n
            )
            self._frames_played += n
            if not self._intent and self._env == 0.0:
                self._fade_done.set()

        mono = self._gen.next_chunk(n).astype(np.float64)
        samples = (mono * env * vol).astype(np.float32)
        outdata[:] = samples.reshape(-1, 1)  # broadcast para todos os canais
