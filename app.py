"""MUSIC_CONVERTER: local audio transcription workbench."""
import hashlib
import io

import pandas as pd
import plotly.graph_objects as go
import pretty_midi
import streamlit as st

from music_converter.pipeline import decode_audio, transcribe, export_files, note_rows, edited_midi, midi_bytes, preview_wav

st.set_page_config(page_title="MUSIC_CONVERTER", page_icon="🎹", layout="wide")
st.title("🎹 MUSIC_CONVERTER")
st.caption("Your recording. Your notes. Processed locally.")
st.info("Phase 1 • Basic Pitch baseline for isolated instruments. High-accuracy piano, full-song separation and piano arrangements are planned; this baseline cannot identify separate instruments or sustain pedal.")
file = st.file_uploader("Upload a recording", type=["mp3", "wav", "flac", "m4a", "ogg", "aac", "aiff", "wma"])
identity = hashlib.sha256(file.getvalue()).hexdigest() if file else None
if st.session_state.get("source_id") != identity:
    for key in ("result", "original", "editor", "files", "preview"):
        st.session_state.pop(key, None)
    st.session_state.source_id = identity
with st.sidebar:
    st.header("Transcription settings")
    st.selectbox("Mode", ["Isolated instrument · Basic Pitch baseline"])
    onset = st.slider("Onset threshold", 0.1, 0.9, 0.5, 0.05)
    frame = st.slider("Sustained-note threshold", 0.1, 0.9, 0.3, 0.05)
    minimum = st.slider("Minimum note duration (ms)", 0, 500, 100, 25)
    quantize = st.checkbox("Quantize score rhythm", value=True, help="Affects MusicXML only. MIDI retains detected timing. Disable for unquantized score export; notation can become complex.")
    st.caption("Thresholds are model activation cutoffs, not calibrated confidence percentages. Set minimum duration to zero to disable short-note filtering.")
if file:
    st.subheader("Original recording")
    st.audio(file)
    if st.button("Transcribe recording", type="primary"):
        for key in ("result", "original", "files", "preview", "editor"):
            st.session_state.pop(key, None)
        progress = st.progress(0, text="Decoding audio…")
        try:
            audio, rate = decode_audio(file.getvalue())
            progress.progress(20, text="Detecting notes with Basic Pitch…")
            midi = transcribe(audio, rate, onset, frame, minimum)
            progress.progress(80, text="Validating MIDI and score exports…")
            files = export_files(midi, quantize)
            st.session_state.update(original=midi_bytes(midi), result=midi_bytes(midi), files=files, preview=preview_wav(midi), export_quantize=quantize)
            progress.progress(100, text="Ready to review")
        except Exception as exc:
            progress.empty()
            st.error(f"Conversion failed: {exc}")
if "result" in st.session_state:
    midi = pretty_midi.PrettyMIDI(io.BytesIO(st.session_state.result))
    rows = note_rows(midi)
    st.subheader(f"Review transcription · {len(rows)} notes")
    st.caption("Synthetic playback preserves note timing and pitch; it does not reproduce piano timbre or pedal. Players can be started and scrubbed separately for comparison.")
    st.audio(st.session_state.preview, format="audio/wav")
    fig = go.Figure()
    for row in rows:
        fig.add_trace(go.Scatter(x=[row["start"], row["end"]], y=[row["pitch"]]*2, mode="lines", line=dict(width=6), showlegend=False, hovertemplate=f"MIDI {row['pitch']} · velocity {row['velocity']}<extra></extra>"))
    fig.update_layout(xaxis_title="Time (seconds)", yaxis_title="MIDI pitch", height=330)
    st.plotly_chart(fig, use_container_width=True)
    with st.form("edit_notes"):
        edited = st.data_editor(pd.DataFrame(rows), num_rows="dynamic", hide_index=True, key="editor")
        apply = st.form_submit_button("Apply edits and rebuild exports")
    if apply or st.session_state.get("export_quantize") != quantize:
        try:
            updated = edited_midi(midi, edited.to_dict("records")) if apply else midi
            files = export_files(updated, quantize)
            st.session_state.update(result=midi_bytes(updated), files=files, preview=preview_wav(updated), export_quantize=quantize)
            st.rerun()
        except Exception as exc:
            st.error(f"Changes were not applied: {exc}")
    st.caption("MIDI downloads contain current edits; the original detected performance remains available separately.")
    st.download_button("Original detected MIDI", st.session_state.original, "original-detected.mid")
    cols = st.columns(5)
    for col, (ext, data) in zip(cols, st.session_state.files.items()):
        mime = "audio/midi" if ext in ("mid", "midi") else "application/vnd.recordare.musicxml" if ext == "mxl" else "application/xml"
        col.download_button(f"Download .{ext}", data, f"transcription.{ext}", mime=mime)
    st.caption("Artie import has not yet been tested. Review the transcription before using it for practice.")
