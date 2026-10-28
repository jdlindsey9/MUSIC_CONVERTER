import copy
import io
import zipfile
from pathlib import Path
import pretty_midi
import pytest
from music21 import stream, note, meter, tempo, bar, converter
from music_converter.scores import import_score
from music_converter.pipeline import export_files
from music_converter.evaluation import compare_notes


def score_fixture():
    s = stream.Score()
    p = stream.Part()
    m = stream.Measure(number=1)
    m.append(meter.TimeSignature('3/4'))
    m.append(tempo.MetronomeMark(number=90))
    m.append(note.Note('C4', quarterLength=1))
    m.append(note.Note('E4', quarterLength=2))
    m.leftBarline = bar.Repeat(direction='start')
    m.rightBarline = bar.Repeat(direction='end')
    p.append(m)
    s.append(p)
    return s


@pytest.mark.parametrize('ext', ['musicxml', 'xml', 'mxl', 'mid', 'midi'])
def test_score_import_and_export(tmp_path, ext):
    s = score_fixture()
    path = tmp_path/('input.'+ext)
    s.write('midi' if ext in ('mid', 'midi') else 'musicxml', fp=path, **({'compress':True} if ext=='mxl' else {}))
    midi, score, recognized = import_score(path.read_bytes(), path.name)
    assert not recognized
    assert {n.pitch for i in midi.instruments for n in i.notes} == {60,64}
    result = export_files(midi, score=score)
    if ext not in ('mid', 'midi'):
        # Native notation survives: meter, tempo, repeats and duration.
        check = converter.parseData(result['musicxml'].decode(), format='musicxml')
        assert check.recurse().getElementsByClass(meter.TimeSignature)[0].ratioString == '3/4'
        assert check.recurse().getElementsByClass(tempo.MetronomeMark)[0].number == 90
        assert isinstance(check.parts[0].measure(1).rightBarline, bar.Repeat)
        assert sum(len(i.notes) for i in midi.instruments) == 2
        assert midi.get_end_time() == pytest.approx(2.0, abs=.01)


def test_repeat_playback_is_explicit(tmp_path):
    path = tmp_path/'repeat.musicxml'
    score_fixture().write('musicxml',fp=path)
    m,_,_ = import_score(path.read_bytes(),path.name,play_once=False)
    assert sum(len(i.notes) for i in m.instruments) == 4


@pytest.mark.parametrize('name,data', [('bad.pdf',b'broken'),('score.xml',b'<not-music/>'),('score.mxl',b'badzip'),('score.exe',b'123')])
def test_bad_scores(name,data):
    with pytest.raises(Exception):
        import_score(data,name,audiveris_path='/missing/audiveris')


def test_accuracy_metric_penalizes_wrong_notes():
    ref=pretty_midi.PrettyMIDI();i=pretty_midi.Instrument(0)
    i.notes=[pretty_midi.Note(80,60,0,1),pretty_midi.Note(80,64,1,2)]
    ref.instruments=[i]
    assert compare_notes(ref,ref)['onset_f1'] == 1
    wrong=copy.deepcopy(ref);wrong.instruments[0].notes[0].pitch=61
    assert compare_notes(ref,wrong)['onset_f1'] == .5
    wrong.instruments[0].notes[1].start += .1
    assert compare_notes(ref,wrong)['onset_f1'] == 0


def test_sheet_ui_import(monkeypatch,tmp_path):
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    path=tmp_path/'input.musicxml';score_fixture().write('musicxml',fp=path)
    uploaded=io.BytesIO(path.read_bytes());uploaded.name=path.name
    monkeypatch.setattr(st,'file_uploader',lambda *a,**k:uploaded)
    app=AppTest.from_file('app.py').run(timeout=30)
    app.radio[0].set_value('Sheet music / MIDI').run()
    app.button[0].click().run(timeout=30)
    assert not app.exception
    assert app.session_state.metadata['mode']=='Sheet music import'
    assert 'imported_score' in app.session_state


def test_transkun_packaging_preserves_model_bytes(tmp_path):
    import importlib.util
    spec=importlib.util.spec_from_file_location('installer','scripts/install_transkun.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    source=tmp_path/'upstream.whl'
    with zipfile.ZipFile(source,'w') as z:
        z.writestr('transkun/model.py',b'print("model")')
        z.writestr('transkun/pretrained/2.0.pt',b'model-weight-bytes')
        z.writestr('transkun-2.0.1.dist-info/METADATA','Version: 2.0.1\nRequires-Dist: ncls\nRequires-Dist: torch\n')
        z.writestr('transkun-2.0.1.dist-info/RECORD','')
    patched=module.patch_wheel(source,tmp_path)
    with zipfile.ZipFile(patched) as z:
        assert z.read('transkun/pretrained/2.0.pt')==b'model-weight-bytes'
        assert z.read('transkun/model.py')==b'print("model")'
        meta=z.read('transkun-'+module.VERSION+'.dist-info/METADATA')
        assert b'Requires-Dist: ncls; extra == "training"' in meta and b'Requires-Dist: torch' in meta


def test_transkun_ui_routes_to_piano_detector(monkeypatch):
    import streamlit as st
    import music_converter.piano_model as backend
    import music_converter.pipeline as pipeline
    from streamlit.testing.v1 import AppTest
    from music_converter.modes import BASELINE
    midi=pretty_midi.PrettyMIDI();inst=pretty_midi.Instrument(0)
    inst.notes=[pretty_midi.Note(90,60,0,1)];midi.instruments=[inst]
    uploaded=io.BytesIO(pipeline.preview_wav(midi));calls=[]
    monkeypatch.setattr(st,'file_uploader',lambda *a,**k:uploaded)
    def detector(audio,rate,device):
        calls.append(device);return midi
    monkeypatch.setattr(backend,'transcribe_piano',detector)
    app=AppTest.from_file('app.py').run(timeout=30)
    app.selectbox[0].select(BASELINE).run()
    app.selectbox[1].select('Transkun V2 (piano)').run()
    app.button[0].click().run(timeout=30)
    assert not app.exception
    assert calls==['auto']
    assert app.session_state.metadata['detector']=='Transkun V2 (piano)'
