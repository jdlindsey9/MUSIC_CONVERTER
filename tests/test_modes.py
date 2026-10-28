import io
import json
import zipfile

import numpy as np
import pretty_midi
import pytest

from music_converter.modes import arrange_piano, separate_piano
from music_converter.pipeline import midi_bytes, note_rows, export_files
from music_converter.delivery import save_results, audio_html, download_html


def dense_fixture():
    midi = pretty_midi.PrettyMIDI(initial_tempo=90)
    inst = pretty_midi.Instrument(24)
    for start, pitches in [(0, [36, 48, 52, 55, 60, 64, 67, 72, 84]), (.5, [38, 50, 53, 57, 62, 65, 69, 74, 86])]:
        for p in pitches:
            inst.notes.append(pretty_midi.Note(80, p, start, start+1))
    inst.notes.append(pretty_midi.Note(90, 60, 0, 1))  # duplicate pitch
    midi.instruments.append(inst)
    drum = pretty_midi.Instrument(0, is_drum=True)
    drum.notes.append(pretty_midi.Note(100, 42, .2, .4))
    midi.instruments.append(drum)
    return midi


@pytest.mark.parametrize('density', [2, 4, 6])
def test_arrangement_constraints(density):
    source = dense_fixture()
    before = midi_bytes(source)
    result = arrange_piano(source, density)
    assert midi_bytes(source) == before
    assert len(result.instruments) == 2
    assert all(i.program == 0 and not i.is_drum for i in result.instruments)
    boundaries = sorted({t for r in note_rows(result) for t in (r['start'], r['end'])})
    for a, b in zip(boundaries, boundaries[1:]):
        t = (a+b)/2
        sounding = [[n for n in inst.notes if n.start <= t < n.end] for inst in result.instruments]
        assert sum(map(len, sounding)) <= density
        for notes in sounding:
            pitches = [n.pitch for n in notes]
            assert len(pitches) == len(set(pitches))
            assert max(pitches, default=0)-min(pitches, default=0) <= 12
    assert {36, 84}.issubset({n.pitch for i in result.instruments for n in i.notes if n.start == 0})
    files = export_files(result)
    reopened = pretty_midi.PrettyMIDI(io.BytesIO(files['mid']))
    assert len(reopened.instruments) == 2


def test_durable_delivery(tmp_path):
    files = export_files(arrange_piano(dense_fixture()))
    path, archive = save_results(files, files['mid'], b'preview', {'mode': 'arrangement'}, root=tmp_path)
    from pathlib import Path
    assert (Path(path)/'transcription.mid').read_bytes() == files['mid']
    assert json.loads((Path(path)/'result.json').read_text())['mode'] == 'arrangement'
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        assert z.read('transcription.mxl') == files['mxl']
    assert 'data:audio/wav;base64,' in audio_html(b'123')
    assert '/media/' not in audio_html(b'123')
    assert 'download="transcription.mid"' in download_html(files['mid'], 'transcription.mid')


def test_isolation_failure_is_not_unseparated_audio(monkeypatch):
    pytest.importorskip('demucs')
    import demucs.pretrained
    def failed(*a, **k):
        raise OSError('network unavailable')
    monkeypatch.setattr(demucs.pretrained, 'get_model', failed)
    with pytest.raises(RuntimeError, match='No unseparated mix'):
        separate_piano(np.zeros((44100, 2)), 44100, 'cpu')


def test_separator_targets_piano_channel(monkeypatch):
    torch = pytest.importorskip('torch')
    pytest.importorskip('demucs')
    import demucs.pretrained
    import demucs.apply
    class Model:
        samplerate = 44100
        sources = ['drums', 'bass', 'other', 'vocals', 'guitar', 'piano']
        def eval(self):
            return self
    monkeypatch.setattr(demucs.pretrained, 'get_model', lambda name: Model())
    def apply(model, wave, **kwargs):
        assert kwargs['device'] == 'cpu'
        out = torch.zeros((1, 6, 2, wave.shape[-1]))
        out[0, 5] = wave[0] * .25
        out[0, 2] = wave[0] * .75
        return out
    monkeypatch.setattr(demucs.apply, 'apply_model', apply)
    audio = np.tile(np.linspace(-1, 1, 44100)[:, None], (1, 2)).astype('float32')
    result, rate = separate_piano(audio, 44100, 'cpu')
    assert rate == 44100
    assert np.allclose(result, audio*.25, atol=1e-5)


def test_app_modes_route_audio_and_clear_stale_results(monkeypatch):
    import streamlit as st
    import music_converter.modes as modes
    import music_converter.pipeline as pipeline
    from streamlit.testing.v1 import AppTest
    fixture = dense_fixture()
    uploaded = io.BytesIO(pipeline.preview_wav(fixture))
    monkeypatch.setattr(st, 'file_uploader', lambda *a, **k: uploaded)
    isolated = np.full((22050, 2), .125, dtype='float32')
    calls = []
    def separator(audio, rate, device):
        assert audio.ndim == 2 and rate == 44100
        calls.append('separate')
        return isolated, 22050
    def detector(audio, rate, *args):
        calls.append('transcribe')
        if calls[0] == 'separate':
            assert audio is isolated
        return fixture
    monkeypatch.setattr(modes, 'separate_piano', separator)
    monkeypatch.setattr(pipeline, 'transcribe', detector)
    app = AppTest.from_file('app.py').run(timeout=30)
    app.button[0].click().run(timeout=30)
    assert not app.exception
    assert calls == ['separate', 'transcribe']
    assert app.session_state.stem is not None
    app.selectbox[0].select(modes.ARRANGEMENT).run()
    assert 'result' not in app.session_state
    calls.clear()
    app.button[0].click().run(timeout=30)
    assert not app.exception
    assert calls == ['transcribe']
    result = pretty_midi.PrettyMIDI(io.BytesIO(app.session_state.result))
    assert len(result.instruments) == 2
    assert app.session_state.stem is None


def test_score_failure_retains_midi(monkeypatch):
    import streamlit as st
    import music_converter.pipeline as pipeline
    from streamlit.testing.v1 import AppTest
    from music_converter.modes import BASELINE
    fixture = dense_fixture()
    uploaded = io.BytesIO(pipeline.preview_wav(fixture))
    monkeypatch.setattr(st, 'file_uploader', lambda *a, **k: uploaded)
    monkeypatch.setattr(pipeline, 'transcribe', lambda *a, **k: fixture)
    def fail(*a, **k):
        raise ValueError('notation failed')
    monkeypatch.setattr(pipeline, 'export_files', fail)
    app = AppTest.from_file('app.py').run(timeout=30)
    app.selectbox[0].select(BASELINE).run()
    app.button[0].click().run(timeout=30)
    assert not app.exception
    assert app.session_state.files['mid'].startswith(b'MThd')
    assert app.session_state.score_error == 'notation failed'
