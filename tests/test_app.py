import os

import numpy as np
import pytest
import soundfile as sf

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt5")

from PyQt5.QtWidgets import QApplication

from audio_viz.app import AudioVizWindow

SAMPLE_RATE = 22050


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture()
def window(qapp, tmp_path):
    path = tmp_path / "tone.wav"
    t = np.arange(2 * SAMPLE_RATE) / SAMPLE_RATE
    sig = 0.5 * np.sin(2 * np.pi * 440 * t)
    sf.write(str(path), sig.astype(np.float32), SAMPLE_RATE)
    win = AudioVizWindow()
    win.open_file(str(path))
    yield win
    win.close()


def test_window_loads_file(window):
    assert window.audio is not None
    assert window.audio.sample_rate == SAMPLE_RATE
    assert "tone.wav" in window.file_label.text()


def test_selection_updates_spectrum(window):
    window.start_spin.setValue(0.5)
    window.end_spin.setValue(1.0)
    line = window.ax_spec.lines[0]
    freqs = line.get_xdata()
    bin_width = SAMPLE_RATE / (window.end_spin.value() - window.start_spin.value())
    assert freqs[-1] == pytest.approx(SAMPLE_RATE / 2.0, abs=bin_width)
    peak_freq = freqs[int(np.argmax(line.get_ydata()))]
    assert peak_freq == pytest.approx(440.0, abs=15.0)


def test_inverted_selection_is_corrected(window):
    window._on_span_selected(1.5, 0.5)
    assert window.start_spin.value() == pytest.approx(0.5)
    assert window.end_spin.value() == pytest.approx(1.5)


def test_spinboxes_clamp_to_duration(window):
    window._on_span_selected(0.1, 99.0)
    assert window.end_spin.value() == pytest.approx(window.audio.duration)
