from __future__ import annotations

import io
import subprocess
import tempfile
import zipfile
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import pretty_midi
import soundfile as sf
from music21 import converter

MAX_SECONDS = 1200
MAX_BYTES = 100 * 1024 * 1024


def decode_audio(data: bytes, rate=22050, channels=1) -> tuple[np.ndarray, int]:
    """Decode by content, never use the client's filename as a filesystem path."""
    if not data or len(data) > MAX_BYTES:
        raise ValueError("Choose a nonempty audio file smaller than 100 MB.")
    with tempfile.TemporaryDirectory() as work:
        source, output = Path(work) / "input", Path(work) / "decoded.wav"
        source.write_bytes(data)
        result = subprocess.run(
            [imageio_ffmpeg.get_ffmpeg_exe(), "-nostdin", "-v", "error", "-y",
             "-i", str(source), "-t", str(MAX_SECONDS + 1), "-vn", "-ac", str(channels),
             "-ar", str(rate), "-c:a", "pcm_f32le", str(output)],
            capture_output=True, timeout=180,
        )
        if result.returncode:
            raise ValueError("Audio could not be decoded. Try a valid WAV, MP3, FLAC or M4A file.")
        audio, rate = sf.read(output, dtype="float32")
    if len(audio) < rate // 10 or len(audio) > MAX_SECONDS * rate:
        raise ValueError("Audio must be between 0.1 seconds and 20 minutes long.")
    if not np.isfinite(audio).all() or np.max(np.abs(audio)) < 1e-6:
        raise ValueError("Audio is silent or contains invalid samples.")
    return audio, rate


def transcribe(audio, rate, onset=0.5, frame=0.3, minimum_ms=100):
    from basic_pitch import ICASSP_2022_MODEL_PATH
    from basic_pitch.inference import predict

    with tempfile.TemporaryDirectory() as work:
        path = Path(work) / "audio.wav"
        sf.write(path, audio, rate)
        _, midi, _ = predict(str(path), model_or_model_path=ICASSP_2022_MODEL_PATH,
                             onset_threshold=onset, frame_threshold=frame,
                             minimum_note_length=minimum_ms)
    return midi


def note_rows(midi):
    return [dict(track=t, pitch=n.pitch, start=n.start, end=n.end, velocity=n.velocity)
            for t, inst in enumerate(midi.instruments) for n in inst.notes]


def edited_midi(original, rows):
    """Keep tempo, instruments and controllers while replacing edited notes."""
    import copy
    midi = copy.deepcopy(original)
    for inst in midi.instruments:
        inst.notes = []
    for row in rows:
        vals = [float(row[k]) for k in ("track", "pitch", "start", "end", "velocity")]
        track, pitch, start, end, velocity = vals
        if not all(np.isfinite(vals)) or not (track.is_integer() and pitch.is_integer() and velocity.is_integer()):
            raise ValueError("Track, pitch and velocity must be finite integers.")
        if not (0 <= track < len(midi.instruments) and 0 <= pitch <= 127 and 1 <= velocity <= 127 and 0 <= start < end <= MAX_SECONDS + 5):
            raise ValueError("Check track, pitch (0–127), velocity (1–127) and start < end.")
        midi.instruments[int(track)].notes.append(pretty_midi.Note(int(velocity), int(pitch), start, end))
    return midi


def midi_bytes(midi):
    out = io.BytesIO()
    midi.write(out)
    return out.getvalue()


def export_files(midi, quantize=True):
    """MIDI retains performance timing; music21 quantization affects only the score."""
    raw = midi_bytes(midi)
    reopened = pretty_midi.PrettyMIDI(io.BytesIO(raw))
    expected = sum(len(i.notes) for i in midi.instruments)
    if not expected:
        raise ValueError("No notes detected. Adjust thresholds or try an isolated instrument.")
    if sum(len(i.notes) for i in reopened.instruments) != expected:
        raise ValueError("MIDI validation failed: note count changed.")
    with tempfile.TemporaryDirectory() as work:
        path = Path(work) / "performance.mid"
        path.write_bytes(raw)
        score = converter.parse(str(path), quantizePost=quantize)
        xml_path = Path(work) / "score.musicxml"
        mxl_path = Path(work) / "compressed.mxl"
        score.write("musicxml", fp=str(xml_path))
        score.write("musicxml", fp=str(mxl_path), compress=True)
        for p in (xml_path, mxl_path):
            check = converter.parse(str(p))
            if not list(check.recurse().notes):
                raise ValueError("Score validation failed: no notes in exported score.")
        if not zipfile.is_zipfile(mxl_path):
            raise ValueError("MXL validation failed: expected a compressed MusicXML archive.")
        return {"mid": raw, "midi": raw, "musicxml": xml_path.read_bytes(),
                "xml": xml_path.read_bytes(), "mxl": mxl_path.read_bytes()}


def preview_wav(midi):
    """Dependency-free synthesis for timing/pitch review, not realistic piano sound."""
    audio = midi.synthesize(fs=22050)
    peak = np.max(np.abs(audio)) if len(audio) else 0
    if peak:
        audio = audio / peak * 0.9
    out = io.BytesIO()
    sf.write(out, audio, 22050, format="WAV", subtype="PCM_16")
    return out.getvalue()


def wav_bytes(audio, rate):
    out = io.BytesIO()
    sf.write(out, audio, rate, format="WAV", subtype="PCM_16")
    return out.getvalue()
