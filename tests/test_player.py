import sys
import threading
import time
import types

import numpy as np
import pytest

from pomodoro import noise as noise_mod
from pomodoro.noise import BrownNoisePlayer


class _Harness:
    def __init__(self) -> None:
        self.created: list = []
        self.fail_open = False
        self.fail_start = False


@pytest.fixture
def harness(monkeypatch):
    h = _Harness()

    class FakeStream:
        def __init__(self, samplerate, blocksize, channels, dtype, callback):
            if h.fail_open:
                raise OSError("Error opening OutputStream: no device")
            self.samplerate = samplerate
            self.blocksize = blocksize
            self.channels = channels
            self.dtype = dtype
            self.callback = callback
            self.started = False
            self.stopped = False
            self.closed = False
            self.close_calls = 0
            h.created.append(self)

        def start(self):
            if h.fail_start:
                raise OSError("start failed")
            self.started = True

        def stop(self):
            self.stopped = True

        def close(self):
            self.closed = True
            self.close_calls += 1

        def run(self, frames):
            """Simula a thread de áudio: invoca a callback com um buffer de saída."""
            out = np.zeros((frames, self.channels), dtype=np.float32)
            self.callback(out, frames, None, None)
            return out

    module = types.ModuleType("sounddevice")
    module.OutputStream = FakeStream
    monkeypatch.setitem(sys.modules, "sounddevice", module)
    # Ruído constante em 1.0 para que a amplitude de saída seja exatamente o envelope * volume.
    monkeypatch.setattr(
        noise_mod.BrownNoiseGenerator,
        "next_chunk",
        lambda self, frames: np.ones(frames, dtype=np.float32),
    )
    return h


def make_player(volume: float = 0.3) -> BrownNoisePlayer:
    # sample_rate 1000 e blocos de 100 frames: 1 bloco = 0.1 s, fades ficam em números redondos.
    return BrownNoisePlayer(sample_rate=1000, volume=volume, block_frames=100)


def test_start_opens_stream_and_plays(harness):
    p = make_player()
    p.start(fade_seconds=0)
    assert p.is_playing
    assert p.is_available
    s = harness.created[0]
    assert s.started
    assert s.samplerate == 1000
    assert s.blocksize == 100
    assert s.channels == 2
    assert callable(s.callback)
    p.close()


def test_start_twice_is_noop(harness):
    p = make_player()
    p.start(fade_seconds=0)
    p.start(fade_seconds=0)
    assert len(harness.created) == 1
    assert p.is_playing
    p.close()


def test_fade_in_amplitude_increases_to_volume_and_is_stereo(harness):
    p = make_player(volume=0.3)
    p.start(fade_seconds=0.5)  # 500 frames
    s = harness.created[0]
    blocks = [s.run(100) for _ in range(10)]

    amps = [float(np.abs(b[:, 0]).max()) for b in blocks]
    assert amps[0] < 0.1
    assert all(a < b for a, b in zip(amps[:5], amps[1:5]))  # crescente durante o fade
    assert amps[-1] == pytest.approx(0.3, abs=1e-6)  # chega ao volume
    for b in blocks:
        np.testing.assert_array_equal(b[:, 0], b[:, 1])  # mono duplicado
    p.close()


def test_set_volume_clamps(harness):
    p = make_player(volume=0.3)
    p.start(fade_seconds=0)
    s = harness.created[0]
    s.run(100)

    p.set_volume(5.0)
    s.run(100)
    last = s.run(100)
    assert float(np.abs(last).max()) == pytest.approx(1.0, abs=1e-6)

    p.set_volume(-2.0)
    s.run(100)
    last = s.run(100)
    assert float(np.abs(last).max()) == pytest.approx(0.0, abs=1e-6)
    p.close()


def test_set_volume_change_is_smooth(harness):
    p = make_player(volume=0.3)
    p.start(fade_seconds=0)
    s = harness.created[0]
    before = s.run(100)

    p.set_volume(0.9)
    after = s.run(100)

    seq = np.concatenate([before[-1:, 0], after[:, 0]]).astype(np.float64)
    max_jump = float(np.abs(np.diff(seq)).max())
    # Rampa de 0.02 s a 1000 Hz = 20 frames para ir de 0 a 1 -> no máximo 1/20 = 0.05 por amostra.
    assert max_jump <= 0.051
    assert after[-1, 0] == pytest.approx(0.9, abs=1e-6)
    p.close()


def test_stop_fades_out_then_closes(harness):
    p = make_player(volume=0.3)
    p.start(fade_seconds=0)
    s = harness.created[0]
    s.run(100)

    t = threading.Thread(target=p.stop, args=(0.1,))
    t.start()
    outs = []
    deadline = time.monotonic() + 3
    while not s.closed and time.monotonic() < deadline:
        outs.append(s.run(20))
        time.sleep(0.001)
    t.join(timeout=3)

    assert s.closed
    assert s.stopped
    assert not p.is_playing
    amps = [float(np.abs(o).max()) for o in outs]
    assert amps[0] > 0.0
    assert all(a >= b - 1e-9 for a, b in zip(amps, amps[1:]))  # nunca sobe durante o fade


def test_stop_with_zero_fade_closes_immediately(harness):
    p = make_player()
    p.start(fade_seconds=0)
    p.stop(fade_seconds=0)
    s = harness.created[0]
    assert s.closed
    assert not p.is_playing


def test_stop_when_not_playing_is_noop(harness):
    p = make_player()
    p.stop()
    assert harness.created == []
    assert not p.is_playing


def test_start_during_stop_fade_cancels_stop(harness):
    p = make_player()
    p.start(fade_seconds=0)
    s = harness.created[0]
    s.run(100)

    t = threading.Thread(target=p.stop, args=(0.5,))
    t.start()
    time.sleep(0.05)
    p.start(fade_seconds=0)
    t.join(timeout=3)

    assert not t.is_alive()
    assert not s.closed
    assert p.is_playing
    assert len(harness.created) == 1
    p.close()


def test_pause_for_alert_silences_then_resumes(harness):
    p = make_player(volume=0.3)
    p.start(fade_seconds=0)
    s = harness.created[0]
    s.run(100)  # frames 0..99, tocando

    p.pause_for_alert(0.2)  # 200 frames: silêncio em 100..299
    assert p.is_playing

    b1 = s.run(100)  # 100..199: fade rápido para zero
    b2 = s.run(100)  # 200..299: silêncio total
    assert float(np.abs(b1).max()) < 0.3
    assert float(np.abs(b2).max()) == pytest.approx(0.0, abs=1e-9)

    b3 = s.run(100)  # 300..399: retomou com fade rápido
    b4 = s.run(100)
    assert float(np.abs(b3).max()) > 0.0
    assert float(np.abs(b4).max()) == pytest.approx(0.3, abs=1e-6)
    assert p.is_playing
    p.close()


def test_pause_when_not_playing_is_noop(harness):
    p = make_player()
    p.pause_for_alert(1.0)
    assert not p.is_playing
    assert harness.created == []


def test_start_without_device_does_not_raise(harness):
    harness.fail_open = True
    p = make_player()
    p.start()  # não deve levantar
    assert not p.is_playing
    assert not p.is_available
    p.close()


def test_start_without_sounddevice_module_does_not_raise(monkeypatch):
    # sys.modules[name] = None faz "import sounddevice" levantar ImportError.
    monkeypatch.setitem(sys.modules, "sounddevice", None)
    p = make_player()
    p.start()
    assert not p.is_playing
    assert not p.is_available


def test_start_stream_failure_leaves_player_stopped(harness):
    harness.fail_start = True
    p = make_player()
    p.start(fade_seconds=0)
    assert not p.is_playing
    assert not p.is_available
    assert harness.created[0].closed


def test_close_is_idempotent(harness):
    p = make_player()
    p.start(fade_seconds=0)
    p.close()
    p.close()
    assert harness.created[0].close_calls == 1
    assert not p.is_playing


def test_close_on_fresh_player_is_safe(harness):
    p = make_player()
    p.close()
    p.close()
    assert not p.is_playing


def test_start_after_close_opens_new_stream(harness):
    p = make_player()
    p.start(fade_seconds=0)
    p.close()
    p.start(fade_seconds=0)
    assert len(harness.created) == 2
    assert p.is_playing
    p.close()


def test_invalid_parameters_raise():
    with pytest.raises(ValueError):
        BrownNoisePlayer(sample_rate=0)
    with pytest.raises(ValueError):
        BrownNoisePlayer(block_frames=0)
