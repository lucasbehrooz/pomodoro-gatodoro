import numpy as np

from pomodoro.noise import BrownNoiseGenerator, apply_gain_ramp


def test_dtype_shape_and_range():
    gen = BrownNoiseGenerator(seed=1)
    x = gen.next_chunk(4096)
    assert x.dtype == np.float32
    assert x.shape == (4096,)
    assert x.min() >= -1.0 and x.max() <= 1.0


def test_zero_frames_returns_empty():
    gen = BrownNoiseGenerator(seed=1)
    x = gen.next_chunk(0)
    assert x.dtype == np.float32
    assert x.shape == (0,)


def test_chunked_equals_single_chunk_with_same_seed():
    total = 5000
    single = BrownNoiseGenerator(seed=42).next_chunk(total)

    gen = BrownNoiseGenerator(seed=42)
    sizes = [1, 7, 64, 100, 333, 1024, 3471]  # soma = 5000, sem múltiplos de bloco
    assert sum(sizes) == total
    chunked = np.concatenate([gen.next_chunk(s) for s in sizes])

    np.testing.assert_allclose(chunked, single, rtol=0, atol=1e-6)


def test_same_seed_same_output():
    a = BrownNoiseGenerator(seed=7).next_chunk(2048)
    b = BrownNoiseGenerator(seed=7).next_chunk(2048)
    np.testing.assert_array_equal(a, b)


def test_different_seeds_different_output():
    a = BrownNoiseGenerator(seed=1).next_chunk(2048)
    b = BrownNoiseGenerator(seed=2).next_chunk(2048)
    assert not np.array_equal(a, b)


def test_reset_reproduces_start():
    gen = BrownNoiseGenerator(seed=3)
    first = gen.next_chunk(1000)
    gen.next_chunk(5000)  # avança o estado
    gen.reset()
    again = gen.next_chunk(1000)
    np.testing.assert_array_equal(first, again)


def test_spectrum_is_brown_not_white():
    sr = 44100
    x = BrownNoiseGenerator(sample_rate=sr, seed=11).next_chunk(sr * 4)
    x = x[sr:]  # descarta o transitório inicial do integrador

    power = np.abs(np.fft.rfft(x)) ** 2
    freqs = np.fft.rfftfreq(x.size, d=1.0 / sr)

    low = power[(freqs >= 20) & (freqs < 200)].mean()
    high = power[(freqs >= 5000) & (freqs < 10000)].mean()

    assert high > 0
    assert low / high > 10.0


def test_not_silent():
    x = BrownNoiseGenerator(seed=5).next_chunk(44100)
    assert float(np.sqrt(np.mean(x.astype(np.float64) ** 2))) > 0.01


def test_no_nan_or_inf_over_many_chunks():
    gen = BrownNoiseGenerator(seed=9)
    for _ in range(100):
        x = gen.next_chunk(4096)
        assert np.all(np.isfinite(x))
        assert x.min() >= -1.0 and x.max() <= 1.0


def test_apply_gain_ramp_endpoints_and_shape():
    rng = np.random.default_rng(0)
    x = rng.uniform(-1, 1, size=1024).astype(np.float32)
    y = apply_gain_ramp(x, 0.0, 1.0)
    assert y.shape == x.shape
    assert y.dtype == np.float32
    np.testing.assert_allclose(y[0], 0.0 * x[0], atol=1e-7)
    np.testing.assert_allclose(y[-1], 1.0 * x[-1], rtol=1e-6)


def test_apply_gain_ramp_fade_out():
    x = np.ones(512, dtype=np.float32)
    y = apply_gain_ramp(x, 1.0, 0.0)
    np.testing.assert_allclose(y[0], 1.0, rtol=1e-6)
    np.testing.assert_allclose(y[-1], 0.0, atol=1e-6)
    assert np.all(np.diff(y) <= 1e-7)  # monotônico


def test_apply_gain_ramp_does_not_mutate_input():
    x = np.ones(16, dtype=np.float32)
    apply_gain_ramp(x, 0.0, 1.0)
    np.testing.assert_array_equal(x, np.ones(16, dtype=np.float32))
