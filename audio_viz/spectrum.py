"""Analyse spectrale d'une fenêtre de signal audio (transformée de Fourier)."""

from __future__ import annotations

import numpy as np


def compute_spectrum(samples: np.ndarray, sample_rate: int):
    """Calcule le spectre d'amplitude (en dB) d'un extrait de signal.

    Applique une fenêtre de Hann puis une FFT. Retourne le tuple
    ``(freqs, magnitude_db)`` pour les fréquences positives uniquement.
    """
    x = np.asarray(samples, dtype=np.float64).ravel()
    n = x.size
    if n == 0:
        return np.empty(0), np.empty(0)
    window = np.hanning(n)
    spectrum = np.fft.rfft(x * window)
    magnitude = np.abs(spectrum) / max(n, 1)
    magnitude_db = 20.0 * np.log10(magnitude + 1e-12)
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    return freqs, magnitude_db


def downsample_waveform(samples: np.ndarray, sample_rate: int, max_points: int = 200_000):
    """Sous-échantillonne un signal pour l'affichage de sa forme d'onde.

    Retourne ``(times, values)``. Pour les grands signaux, un min/max par
    segment est conservé afin de ne pas perdre les crêtes.
    """
    x = np.asarray(samples, dtype=np.float64).ravel()
    n = x.size
    if n <= max_points:
        return np.arange(n) / float(sample_rate), x
    block = int(np.ceil(n / max_points))
    trimmed = n - (n % block)
    blocks = x[:trimmed].reshape(-1, block)
    mins = blocks.min(axis=1)
    maxs = blocks.max(axis=1)
    values = np.empty(2 * blocks.shape[0])
    values[0::2] = mins
    values[1::2] = maxs
    times = (np.arange(blocks.shape[0]) * block) / float(sample_rate)
    times = np.repeat(times, 2)
    return times, values
