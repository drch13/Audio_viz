"""Interface graphique de visualisation d'un signal audio.

Fenêtre principale : la forme d'onde du signal est affichée en haut avec un
sélecteur de plage (glisser-déposer pour choisir début et fin, en secondes) ;
le spectre (FFT, échelle dB) de la fenêtre sélectionnée est affiché en dessous
et se met à jour à chaque changement de sélection.
"""

from __future__ import annotations

import os

import numpy as np

import matplotlib

matplotlib.use("Qt5Agg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .audio_loader import AudioData, load_audio
from .spectrum import compute_spectrum, downsample_waveform

AUDIO_FILE_FILTER = (
    "Fichiers audio (*.wav *.mp3 *.wma *.ogg *.oga *.flac *.aac *.m4a *.opus *.aiff *.aif);;"
    "Tous les fichiers (*)"
)


class AudioVizWindow(QMainWindow):
    """Fenêtre principale de l'application."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Audio_viz — Visualisation de signal audio")
        self.resize(1100, 800)

        self.audio: AudioData | None = None
        self._wave_times: np.ndarray | None = None
        self._wave_values: np.ndarray | None = None
        self._selector: SpanSelector | None = None
        self._updating_spinboxes = False

        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        controls = QHBoxLayout()
        self.open_button = QPushButton("Ouvrir un fichier audio…", self)
        self.open_button.clicked.connect(self.open_file)
        controls.addWidget(self.open_button)

        self.file_label = QLabel("Aucun fichier chargé")
        controls.addWidget(self.file_label, stretch=1)

        controls.addWidget(QLabel("Début (s) :"))
        self.start_spin = QDoubleSpinBox()
        self.start_spin.setRange(0.0, 0.0)
        self.start_spin.setDecimals(3)
        self.start_spin.setSingleStep(0.01)
        self.start_spin.valueChanged.connect(self._on_spinbox_changed)
        controls.addWidget(self.start_spin)

        controls.addWidget(QLabel("Fin (s) :"))
        self.end_spin = QDoubleSpinBox()
        self.end_spin.setRange(0.0, 0.0)
        self.end_spin.setDecimals(3)
        self.end_spin.setSingleStep(0.01)
        self.end_spin.valueChanged.connect(self._on_spinbox_changed)
        controls.addWidget(self.end_spin)

        self.zoom_button = QPushButton("Zoomer sur la sélection")
        self.zoom_button.clicked.connect(self._zoom_on_selection)
        controls.addWidget(self.zoom_button)

        layout.addLayout(controls)

        self.figure = Figure(figsize=(10, 7))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas, stretch=1)

        self.ax_wave = self.figure.add_subplot(2, 1, 1)
        self.ax_wave.set_ylabel("Amplitude")
        self.ax_wave.set_title("Signal audio — glissez sur le graphique pour sélectionner une fenêtre")
        self.ax_wave.grid(True, alpha=0.3)

        self.ax_spec = self.figure.add_subplot(2, 1, 2)
        self.ax_spec.set_xlabel("Fréquence (Hz)")
        self.ax_spec.set_ylabel("Intensité (dB)")
        self.ax_spec.set_title("Spectre de la fenêtre sélectionnée (FFT)")
        self.ax_spec.grid(True, alpha=0.3)

        self.figure.tight_layout()

    # ------------------------------------------------------------- chargement
    def open_file(self, path: str | None = None) -> None:
        if path is None:
            path, _ = QFileDialog.getOpenFileName(self, "Ouvrir un fichier audio", "", AUDIO_FILE_FILTER)
        if not path:
            return
        try:
            self.audio = load_audio(path)
        except Exception as exc:
            QMessageBox.critical(self, "Erreur de lecture", f"Impossible de lire {path} :\n{exc}")
            return
        self._setup_after_load(os.path.basename(path))

    def _setup_after_load(self, name: str) -> None:
        assert self.audio is not None
        duration = self.audio.duration
        self.file_label.setText(
            f"{name} — {duration:.3f} s — {self.audio.sample_rate} Hz"
        )
        self._updating_spinboxes = True
        try:
            self.start_spin.setRange(0.0, duration)
            self.end_spin.setRange(0.0, duration)
            self.start_spin.setValue(0.0)
            self.end_spin.setValue(min(duration, 1.0) if duration > 1.0 else duration)
        finally:
            self._updating_spinboxes = False

        self._wave_times, self._wave_values = downsample_waveform(
            self.audio.samples, self.audio.sample_rate
        )
        self.ax_wave.clear()
        self.ax_wave.set_ylabel("Amplitude")
        self.ax_wave.set_xlabel("Temps (s)")
        self.ax_wave.set_title(
            "Signal audio — glissez sur le graphique pour sélectionner une fenêtre"
        )
        self.ax_wave.grid(True, alpha=0.3)
        self.ax_wave.plot(self._wave_times, self._wave_values, linewidth=0.5, color="#1f77b4")
        self.ax_wave.set_xlim(0.0, duration)

        if self._selector is not None:
            self._selector.disconnect_events()
        self._selector = SpanSelector(
            self.ax_wave,
            onselect=self._on_span_selected,
            direction="horizontal",
            useblit=True,
            props=dict(alpha=0.25, facecolor="#ff7f0e"),
            interactive=True,
            drag_from_anywhere=True,
        )
        self.canvas.draw_idle()
        self._update_spectrum()

    # ------------------------------------------------------------ événements
    def _on_span_selected(self, xmin: float, xmax: float) -> None:
        if self.audio is None or self._updating_spinboxes:
            return
        duration = self.audio.duration
        xmin = min(max(xmin, 0.0), duration)
        xmax = min(max(xmax, 0.0), duration)
        if xmax < xmin:
            xmin, xmax = xmax, xmin
        self._updating_spinboxes = True
        try:
            self.start_spin.setValue(xmin)
            self.end_spin.setValue(xmax)
        finally:
            self._updating_spinboxes = False
        self._update_spectrum()

    def _on_spinbox_changed(self) -> None:
        if self.audio is None or self._updating_spinboxes:
            return
        start = self.start_spin.value()
        end = self.end_spin.value()
        if end < start:
            end = start
            self._updating_spinboxes = True
            self.end_spin.setValue(end)
            self._updating_spinboxes = False
        if self._selector is not None:
            self._selector.extents = (start, end)
        self._update_spectrum()

    def _zoom_on_selection(self) -> None:
        if self.audio is None:
            return
        start = self.start_spin.value()
        end = self.end_spin.value()
        if end <= start:
            return
        self.ax_wave.set_xlim(start, end)
        self.canvas.draw_idle()

    # -------------------------------------------------------------- affichage
    def _update_spectrum(self) -> None:
        self.ax_spec.clear()
        self.ax_spec.set_xlabel("Fréquence (Hz)")
        self.ax_spec.set_ylabel("Intensité (dB)")
        self.ax_spec.grid(True, alpha=0.3)
        if self.audio is None:
            self.ax_spec.set_title("Spectre de la fenêtre sélectionnée (FFT)")
            self.canvas.draw_idle()
            return
        start = self.start_spin.value()
        end = self.end_spin.value()
        segment = self.audio.slice(start, end)
        title = f"Spectre de la fenêtre [{start:.3f} s ; {end:.3f} s] (FFT)"
        if segment.size == 0:
            self.ax_spec.set_title(title + " — fenêtre vide")
            self.canvas.draw_idle()
            return
        freqs, magnitude_db = compute_spectrum(segment, self.audio.sample_rate)
        self.ax_spec.plot(freqs, magnitude_db, linewidth=0.8, color="#2ca02c")
        self.ax_spec.set_xlim(0.0, self.audio.sample_rate / 2.0)
        self.ax_spec.set_title(title)
        self.canvas.draw_idle()


def main(argv: list[str] | None = None) -> int:
    import sys

    app = QApplication(argv if argv is not None else sys.argv)
    window = AudioVizWindow()
    window.show()
    args = argv if argv is not None else sys.argv[1:]
    if args and os.path.isfile(args[0]):
        window.open_file(args[0])
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
