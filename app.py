"""Local transcription, experimental piano isolation and generated arrangements."""
import hashlib
import io

import pandas as pd
import plotly.graph_objects as go
import pretty_midi
import streamlit as st
import streamlit.components.v1 as components

from music_converter.pipeline import decode_audio, transcribe, export_files, note_rows, edited_midi, midi_bytes, preview_wav, wav_bytes
from music_converter.modes import PIANO, ARRANGEMENT, BASELINE, separate_piano, arrange_piano
from music_converter.delivery import audio_html, download_html, save_results

st.set_page_config(page_title="MUSIC_CONVERTER", page_icon="🎹", layout="wide")
st.title("🎹 MUSIC_CONVERTER")
st.caption("Your recording. Your notes. Processed locally.")


def clear_results():
    for key in ('result', 'original', 'files', 'preview', 'stem', 'metadata', 'saved_path', 'archive', 'score_error', 'save_error'):
        st.session_state.pop(key, None)
    st.session_state.edit_version = st.session_state.get('edit_version', 0) + 1


def publish(midi, original, metadata, stem=None):
    raw = midi_bytes(midi)
    if not note_rows(midi):
        raise ValueError('No notes detected. Try a different recording or adjust the thresholds.')
    score_error = None
    try:
        files = export_files(midi, quantize)
    except Exception as exc:
        files = {'mid': raw, 'midi': raw}
        score_error = str(exc)
    preview = preview_wav(midi)
    # A score or disk-write failure must not hide a valid MIDI result.
    saved_path, archive, save_error = None, None, None
    try:
        saved_path, archive = save_results(files, original, preview, metadata, stem)
    except OSError as exc:
        save_error = str(exc)
    st.session_state.update(result=raw, original=original, files=files, preview=preview,
                            stem=stem, metadata=metadata, saved_path=saved_path, archive=archive,
                            score_error=score_error, save_error=save_error, export_quantize=quantize)
    st.session_state.edit_version = st.session_state.get('edit_version', 0) + 1


with st.sidebar:
    st.header('Transcription settings')
    mode = st.selectbox('Mode', [PIANO, ARRANGEMENT, BASELINE])
    device = st.selectbox('Separation device', ['auto', 'cuda', 'cpu'], disabled=mode != PIANO)
    density = st.slider('Arrangement: maximum simultaneous notes', 2, 6, 4, disabled=mode != ARRANGEMENT)
    onset = st.slider('Onset threshold', 0.1, 0.9, 0.5, 0.05)
    frame = st.slider('Sustained-note threshold', 0.1, 0.9, 0.3, 0.05)
    minimum = st.slider('Minimum note duration (ms)', 0, 500, 100, 25)
    quantize = st.checkbox('Quantize score rhythm', value=True, help='Affects MusicXML only. MIDI retains performance timing.')
    st.caption('Thresholds are model activation cutoffs, not calibrated confidence percentages. Basic Pitch does not estimate song tempo.')
if mode == PIANO:
    st.info('Extract the existing piano with Demucs, then transcribe that stem. Listen to the isolated audio before trusting the notes. Other instruments can leak through; this is experimental.')
    st.caption('One-time setup: close the app, run INSTALL_PIANO_WINDOWS.bat in its folder, choose G for your NVIDIA GPU, then restart. First isolation downloads model weights. CPU is supported but slower.')
elif mode == ARRANGEMENT:
    st.info('Generated piano arrangement: reduce notes from the whole recording to melody, bass and supporting harmony, split into two hand tracks. This is a heuristic draft, not an exact transcription or guaranteed playable arrangement.')
else:
    st.info('Transcribe audio that already contains an isolated instrument. This option does not separate instruments.')
file = st.file_uploader('Upload a recording', type=['mp3', 'wav', 'flac', 'm4a', 'ogg', 'aac', 'aiff', 'wma'])
identity = hashlib.sha256(file.getvalue()).hexdigest() if file else None
result_key = (identity, mode, density if mode == ARRANGEMENT else None)
if st.session_state.get('source_key') != result_key:
    clear_results()
    st.session_state.source_key = result_key
if file:
    st.subheader('Original recording')
    name = str(getattr(file, 'name', 'recording.wav'))
    ext = name.rsplit('.', 1)[-1].lower()
    mime = {'mp3': 'audio/mpeg', 'm4a': 'audio/mp4', 'flac': 'audio/flac', 'ogg': 'audio/ogg', 'aac': 'audio/aac'}.get(ext, 'audio/wav')
    components.html(audio_html(file.getvalue(), mime), height=65)
    if st.button('Transcribe recording', type='primary'):
        clear_results()
        progress = st.progress(0, text='Decoding audio…')
        try:
            stem = None
            if mode == PIANO:
                audio, rate = decode_audio(file.getvalue(), rate=44100, channels=2)
                progress.progress(10, text='Isolating piano (first run downloads weights)…')
                audio, rate = separate_piano(audio, rate, device)
                stem = wav_bytes(audio, rate)
            else:
                audio, rate = decode_audio(file.getvalue())
            progress.progress(45, text='Detecting notes with Basic Pitch…')
            detected = transcribe(audio, rate, onset, frame, minimum)
            midi = arrange_piano(detected, density) if mode == ARRANGEMENT else detected
            if mode == PIANO:
                for inst in midi.instruments:
                    inst.program, inst.name = 0, 'Piano - experimental isolation'
            progress.progress(80, text='Preparing playback and saving files…')
            metadata = dict(mode=mode, source_sha256=identity, onset=onset, frame=frame,
                            minimum_ms=minimum, density=density if mode == ARRANGEMENT else None,
                            quantized_score=quantize, device=device if mode == PIANO else 'cpu')
            publish(midi, midi_bytes(detected), metadata, stem)
            progress.progress(100, text='Ready to review')
        except Exception as exc:
            progress.empty()
            st.error(f'Conversion failed: {exc}')
if 'result' in st.session_state:
    midi = pretty_midi.PrettyMIDI(io.BytesIO(st.session_state.result))
    rows = note_rows(midi)
    if st.session_state.stem:
        st.subheader('Isolated piano audio — check for other instruments')
        components.html(audio_html(st.session_state.stem), height=65)
        st.download_button('Download isolated piano audio', st.session_state.stem, 'isolated-piano.wav', 'audio/wav', on_click='ignore')
    st.subheader(f'Review transcription · {len(rows)} notes')
    st.caption('Synthetic note playback uses simple tones, not a recorded piano sound. Arrangement mode reduces density but cannot repair incorrect model detections.')
    components.html(audio_html(st.session_state.preview), height=65)
    fig = go.Figure()
    # One trace per track rather than one trace per note keeps long songs responsive.
    for track, inst in enumerate(midi.instruments):
        x, y = [], []
        for n in inst.notes:
            x.extend([n.start, n.end, None])
            y.extend([n.pitch, n.pitch, None])
        fig.add_trace(go.Scattergl(x=x, y=y, mode='lines', line=dict(width=5), name=inst.name or f'Track {track}'))
    fig.update_layout(xaxis_title='Time (seconds)', yaxis_title='MIDI pitch', height=330)
    st.plotly_chart(fig, use_container_width=True)
    with st.form('edit_notes'):
        edited = st.data_editor(pd.DataFrame(rows), num_rows='dynamic', hide_index=True, key=f'editor_{st.session_state.edit_version}')
        apply = st.form_submit_button('Apply edits and rebuild exports')
    if apply or st.session_state.get('export_quantize') != quantize:
        try:
            updated = edited_midi(midi, edited.to_dict('records')) if apply else midi
            metadata = dict(st.session_state.metadata, quantized_score=quantize)
            publish(updated, st.session_state.original, metadata, st.session_state.stem)
            st.rerun()
        except Exception as exc:
            st.error(f'Changes were not applied: {exc}')
    if st.session_state.score_error:
        st.warning(f'MIDI is available, but score export failed: {st.session_state.score_error}')
    if st.session_state.saved_path:
        st.success('Files also saved on this computer. If a browser download fails, open this folder in File Explorer:')
        st.code(st.session_state.saved_path, language=None)
    elif st.session_state.save_error:
        st.warning(f'Could not save files on disk: {st.session_state.save_error}')
    st.download_button('Original detected MIDI', st.session_state.original, 'original-detected.mid', on_click='ignore')
    cols = st.columns(5)
    for col, (ext, data) in zip(cols, st.session_state.files.items()):
        mime = 'audio/midi' if ext in ('mid', 'midi') else 'application/vnd.recordare.musicxml' if ext == 'mxl' else 'application/xml'
        col.download_button(f'Download .{ext}', data, f'transcription.{ext}', mime=mime, on_click='ignore')
    components.html(download_html(st.session_state.result, 'transcription.mid'), height=35)
    if st.session_state.archive:
        st.download_button('Download all files (.zip)', st.session_state.archive, 'transcription.zip', 'application/zip', on_click='ignore')
    st.caption('Artie import remains unverified. Keep the app running while using browser downloads. Local files remain available after closing it.')
