import io

import numpy as np
import pytest
import soundfile as sf

from audio_viz.audio_loader import AudioData, load_audio, load_audio_bytes

SAMPLE_RATE = 22050


def make_tone(freq=440.0, duration=1.0, sr=SAMPLE_RATE):
    t = np.arange(int(duration * sr)) / sr
    return (0.5 * np.sin(2 * np.pi * freq * t)).astype(np.float32)


@pytest.fixture()
def wav_path(tmp_path):
    path = tmp_path / "tone.wav"
    sf.write(str(path), make_tone(), SAMPLE_RATE)
    return str(path)


@pytest.fixture()
def stereo_wav_path(tmp_path):
    path = tmp_path / "stereo.wav"
    sig = make_tone()
    stereo = np.stack([sig, -sig], axis=1)
    sf.write(str(path), stereo, SAMPLE_RATE)
    return str(path)


def test_load_wav(wav_path):
    audio = load_audio(wav_path)
    assert audio.sample_rate == SAMPLE_RATE
    assert abs(audio.duration - 1.0) < 1e-3
    assert audio.samples.ndim == 1
    assert float(np.abs(audio.samples).max()) <= 1.0


def test_load_missing_file():
    with pytest.raises(FileNotFoundError):
        load_audio("/nonexistent/file.wav")


def test_stereo_is_downmixed_to_mono(stereo_wav_path):
    audio = load_audio(stereo_wav_path)
    assert audio.samples.ndim == 1
    # Les deux canaux sont opposés : le mixage doit donner ~0.
    assert float(np.abs(audio.samples).max()) < 1e-3


def test_slice():
    audio = AudioData(samples=make_tone(duration=2.0), sample_rate=SAMPLE_RATE)
    segment = audio.slice(0.5, 1.0)
    assert len(segment) == pytest.approx(0.5 * SAMPLE_RATE, abs=2)
    assert len(audio.slice(1.843, 1.543)) == 0  # bornes inversées -> vide
    assert len(audio.slice(-5.0, 99.0)) == len(audio.samples)  # bornes bornées


@pytest.mark.parametrize("fmt", ["wav", "flac", "ogg"])
def test_load_native_formats(tmp_path, fmt):
    sig = make_tone()
    path = tmp_path / f"tone.{fmt}"
    sf.write(str(path), sig, SAMPLE_RATE, format=fmt.upper() if fmt != "ogg" else "OGG")
    audio = load_audio(str(path))
    assert audio.sample_rate == SAMPLE_RATE
    assert audio.samples.ndim == 1


@pytest.mark.parametrize("fmt", ["mp3", "wma", "m4a"])
def test_load_compressed_formats_via_ffmpeg(tmp_path, fmt):
    pytest.importorskip("imageio_ffmpeg")
    from pydub import AudioSegment
    import imageio_ffmpeg

    AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
    AudioSegment.ffprobe = imageio_ffmpeg.get_ffmpeg_exe()

    ext = {"m4a": "mp4", "wma": "asf"}.get(fmt, fmt)
    codec = {"m4a": "aac", "wma": "wmav2"}.get(fmt)
    path = tmp_path / f"tone.{fmt}"
    seg = AudioSegment.from_wav(io.BytesIO(_wav_bytes(make_tone())))
    kwargs = {"format": ext}
    if codec:
        kwargs["codec"] = codec
    seg.export(str(path), **kwargs)

    audio = load_audio(str(path))
    assert audio.sample_rate > 0
    assert audio.samples.size > 0
    assert float(np.abs(audio.samples).max()) > 0.1  # signal non nul


def test_load_audio_bytes_wav():
    audio = load_audio_bytes(_wav_bytes(make_tone()), suffix=".wav")
    assert audio.sample_rate == SAMPLE_RATE
    assert abs(audio.duration - 1.0) < 1e-3


def _wav_bytes(sig):
    buf = io.BytesIO()
    sf.write(buf, sig, SAMPLE_RATE, format="WAV")
    return buf.getvalue()
