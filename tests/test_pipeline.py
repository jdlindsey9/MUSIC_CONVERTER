import io
import zipfile

import numpy as np
import pretty_midi
import pytest
import soundfile as sf
from music21 import converter
from streamlit.testing.v1 import AppTest

from music_converter.pipeline import decode_audio, edited_midi, export_files, note_rows, preview_wav


def fixture_midi():
    midi = pretty_midi.PrettyMIDI(initial_tempo=100)
    for program, pitches in [(0, [60, 64, 67]), (32, [36])]:
        inst = pretty_midi.Instrument(program)
        for p in pitches:
            inst.notes.append(pretty_midi.Note(90, p, 0.13, 1.37))
        midi.instruments.append(inst)
    return midi


@pytest.mark.parametrize('quantize', [True, False])
def test_exports(tmp_path, quantize):
    midi = fixture_midi()
    files = export_files(midi, quantize)
    for ext in ('mid', 'midi'):
        check = pretty_midi.PrettyMIDI(io.BytesIO(files[ext]))
        assert len(check.instruments) == 2
        for expected, actual in zip(note_rows(midi), note_rows(check)):
            assert actual['pitch'] == expected['pitch']
            assert actual['start'] == pytest.approx(expected['start'], abs=.003)
            assert actual['end'] == pytest.approx(expected['end'], abs=.003)
    for ext in ('musicxml', 'xml', 'mxl'):
        path = tmp_path / ('score.' + ext)
        path.write_bytes(files[ext])
        score = converter.parse(path)
        assert len(score.parts) == 2
        assert {p.midi for n in score.recurse().notes for p in n.pitches} == {36, 60, 64, 67}
    with zipfile.ZipFile(io.BytesIO(files['mxl'])) as archive:
        assert 'META-INF/container.xml' in archive.namelist()


def test_edit_preserves_original():
    midi = fixture_midi()
    rows = note_rows(midi)
    rows[0]['pitch'] = 72
    edited = edited_midi(midi, rows)
    assert midi.instruments[0].notes[0].pitch == 60
    assert edited.instruments[0].notes[0].pitch == 72
    rows[0]['end'] = -1
    with pytest.raises(ValueError):
        edited_midi(midi, rows)


@pytest.mark.parametrize('data', [b'', b'corrupted audio'])
def test_bad_audio(data):
    with pytest.raises(ValueError):
        decode_audio(data)


def test_decode_and_preview():
    data = preview_wav(fixture_midi())
    audio, rate = decode_audio(data)
    assert rate == 22050 and np.max(np.abs(audio)) > 0
    silent = io.BytesIO()
    sf.write(silent, np.zeros(22050), 22050, format='WAV')
    with pytest.raises(ValueError, match='silent'):
        decode_audio(silent.getvalue())


def test_empty_export():
    with pytest.raises(ValueError, match='No notes'):
        export_files(pretty_midi.PrettyMIDI())


def test_app_starts():
    app = AppTest.from_file('app.py').run(timeout=30)
    assert not app.exception
    assert app.title[0].value == '🎹 MUSIC_CONVERTER'


@pytest.mark.parametrize('suffix', ['mp3', 'flac', 'm4a', 'ogg', 'wav'])
def test_common_formats(tmp_path, suffix):
    import subprocess
    import imageio_ffmpeg
    source = tmp_path / 'source.wav'
    source.write_bytes(preview_wav(fixture_midi()))
    output = tmp_path / ('encoded.' + suffix)
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error', '-y', '-i', str(source), str(output)], check=True)
    audio, rate = decode_audio(output.read_bytes())
    assert rate == 22050 and len(audio) > rate


def test_upload_workflow(monkeypatch):
    """AppTest does not expose uploads: inject bytes at the upload widget boundary."""
    import streamlit as st
    uploaded = io.BytesIO(preview_wav(fixture_midi()))
    monkeypatch.setattr(st, 'file_uploader', lambda *a, **k: uploaded)
    import music_converter.pipeline as pipeline
    monkeypatch.setattr(pipeline, 'transcribe', lambda *a, **k: fixture_midi())
    app = AppTest.from_file('app.py').run(timeout=30)
    app.selectbox[0].select('Already isolated instrument (baseline)').run()
    app.button[0].click().run(timeout=30)
    assert not app.exception
    assert 'result' in app.session_state
    uploaded.seek(0)
    uploaded.truncate()
    uploaded.write(b'new recording')
    app.run()
    assert 'result' not in app.session_state
    app.button[0].click().run(timeout=30)
    assert not app.exception
    assert 'could not be decoded' in app.error[0].value
