import numpy as np
import pytest

from audio_viz.spectrum import compute_spectrum, downsample_waveform

SAMPLE_RATE = 8000


def test_spectrum_peak_at_tone_frequency():
    t = np.arange(SAMPLE_RATE) / SAMPLE_RATE  # 1 s
    tone = np.sin(2 * np.pi * 1000.0 * t)
    freqs, magnitude_db = compute_spectrum(tone, SAMPLE_RATE)
    peak_freq = freqs[int(np.argmax(magnitude_db))]
    assert peak_freq == pytest.approx(1000.0, abs=5.0)


def test_spectrum_only_positive_frequencies():
    t = np.arange(2048) / SAMPLE_RATE
    freqs, magnitude_db = compute_spectrum(np.sin(2 * np.pi * 440 * t), SAMPLE_RATE)
    assert freqs[0] == 0.0
    assert freqs[-1] == pytest.approx(SAMPLE_RATE / 2.0)
    assert len(freqs) == len(magnitude_db) == 2048 // 2 + 1
    assert np.all(np.isfinite(magnitude_db))


def test_spectrum_empty_input():
    freqs, magnitude_db = compute_spectrum(np.empty(0), SAMPLE_RATE)
    assert len(freqs) == 0
    assert len(magnitude_db) == 0


def test_silence_is_very_low():
    _, magnitude_db = compute_spectrum(np.zeros(1024), SAMPLE_RATE)
    assert magnitude_db.max() < -100.0


def test_downsample_short_signal_unchanged():
    sig = np.linspace(-1, 1, 1000)
    times, values = downsample_waveform(sig, SAMPLE_RATE, max_points=200_000)
    assert len(times) == len(values) == 1000
    np.testing.assert_allclose(values, sig)
    assert times[-1] == pytest.approx(999 / SAMPLE_RATE)


def test_downsample_long_signal_preserves_extremes():
    sig = np.zeros(100_000)
    sig[500] = 1.0
    sig[99_500] = -1.0
    times, values = downsample_waveform(sig, SAMPLE_RATE, max_points=1_000)
    assert len(values) <= 2_000
    assert values.max() == pytest.approx(1.0)
    assert values.min() == pytest.approx(-1.0)
    assert times[0] == 0.0
