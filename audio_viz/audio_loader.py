"""Chargement de signaux audio dans plusieurs formats (wav, flac, ogg, mp3, wma, ...).

Les formats supportés nativement par libsndfile (WAV, FLAC, OGG/Vorbis) sont lus
directement avec :mod:`soundfile`. Tous les autres formats (MP3, WMA, AAC, M4A,
OPUS, ...) sont décodés en WAV mono via ``ffmpeg`` (binaire embarqué par
``imageio-ffmpeg`` ou ``ffmpeg`` présent sur le système).
"""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass

import numpy as np
import soundfile as sf


@dataclass
class AudioData:
    """Signal audio mono normalisé avec sa fréquence d'échantillonnage."""

    samples: np.ndarray  # tableau 1-D de flottants dans [-1, 1]
    sample_rate: int

    @property
    def duration(self) -> float:
        """Durée du signal en secondes."""
        return float(len(self.samples)) / float(self.sample_rate)

    def slice(self, start: float, end: float) -> np.ndarray:
        """Extrait les échantillons entre ``start`` et ``end`` (en secondes)."""
        i0 = max(0, int(round(start * self.sample_rate)))
        i1 = min(len(self.samples), int(round(end * self.sample_rate)))
        return self.samples[i0:i1]


def _ffmpeg_executable() -> str:
    """Retourne le chemin de ffmpeg : variable d'env, PATH, ou imageio-ffmpeg."""
    env = os.environ.get("FFMPEG_PATH") or os.environ.get("AUDIO_VIZ_FFMPEG")
    if env:
        return env
    on_path = shutil.which("ffmpeg")
    if on_path:
        return on_path
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as exc:  # pragma: no cover - dépend de l'installation
        raise RuntimeError(
            "ffmpeg est requis pour décoder ce format. "
            "Installez-le (apt install ffmpeg) ou `pip install imageio-ffmpeg`, "
            "ou définissez la variable d'environnement FFMPEG_PATH."
        ) from exc


def _load_with_soundfile(path: str) -> AudioData:
    data, sample_rate = sf.read(path, dtype="float32", always_2d=True)
    mono = data.mean(axis=1)
    return AudioData(samples=np.ascontiguousarray(mono), sample_rate=int(sample_rate))


def _load_with_ffmpeg(path: str) -> AudioData:
    ffmpeg = _ffmpeg_executable()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name
    try:
        subprocess.run(
            [ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
             "-i", path, "-ac", "1", "-f", "wav", wav_path],
            check=True,
        )
        return _load_with_soundfile(wav_path)
    finally:
        try:
            os.unlink(wav_path)
        except OSError:
            pass


def load_audio(path: str) -> AudioData:
    """Charge un fichier audio et retourne un signal mono.

    Essaie d'abord une lecture directe (soundfile/libsndfile), puis bascule sur
    un décodage ffmpeg pour les formats compressés (mp3, wma, aac, m4a, ...).
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    try:
        return _load_with_soundfile(path)
    except (sf.SoundFileError, RuntimeError, ValueError):
        return _load_with_ffmpeg(path)


def load_audio_bytes(raw: bytes, suffix: str = "") -> AudioData:
    """Charge un signal audio depuis des octets en mémoire (utile pour les tests)."""
    try:
        data, sample_rate = sf.read(io.BytesIO(raw), dtype="float32", always_2d=True)
        mono = data.mean(axis=1)
        return AudioData(samples=np.ascontiguousarray(mono), sample_rate=int(sample_rate))
    except (sf.SoundFileError, RuntimeError, ValueError):
        ffmpeg = _ffmpeg_executable()
        with tempfile.NamedTemporaryFile(suffix=suffix or ".bin", delete=False) as src:
            src.write(raw)
            src_path = src.name
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as dst:
            wav_path = dst.name
        try:
            subprocess.run(
                [ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                 "-i", src_path, "-ac", "1", "-f", "wav", wav_path],
                check=True,
            )
            return _load_with_soundfile(wav_path)
        finally:
            for p in (src_path, wav_path):
                try:
                    os.unlink(p)
                except OSError:
                    pass
