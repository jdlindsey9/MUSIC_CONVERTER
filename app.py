"""MUSIC_CONVERTER: local-first audio to MIDI and MusicXML prototype."""
from __future__ import annotations
import tempfile
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="MUSIC_CONVERTER", page_icon="🎹", layout="centered")
st.title("🎹 MUSIC_CONVERTER")
st.caption("Local audio → MIDI → MusicXML. Single-instrument prototype; no guarantee of perfect transcription.")
st.info("Best results: isolated piano or a single instrument. Full mixed songs and separate instrumental tracks require additional models.")
file = st.file_uploader("Upload your audio", type=["mp3", "wav", "flac", "m4a", "ogg"])
min_note_length = st.slider("Minimum note duration (ms)", 50, 500, 100, 25)
confidence = st.slider("Minimum confidence", 0.1, 0.9, 0.3, 0.05)
if file:
    st.audio(file)
    if st.button("Transcribe audio", type="primary"):
        with st.spinner("Analyzing notes locally — first run may download model weights..."):
            try:
                from basic_pitch.inference import predict
                from basic_pitch import ICASSP_2022_MODEL_PATH
                from music21 import converter
                import pretty_midi
                with tempfile.TemporaryDirectory() as work:
                    src = Path(work) / Path(file.name).name
                    src.write_bytes(file.getvalue())
                    _, midi_data, _ = predict(
                        str(src),
                        model_or_model_path=ICASSP_2022_MODEL_PATH,
                        onset_threshold=confidence,
                        minimum_note_length=min_note_length,
                    )
                    midi_path = Path(work) / "transcription.mid"
                    midi_data.write(str(midi_path))
                    midi_bytes = midi_path.read_bytes()
                    pm = pretty_midi.PrettyMIDI(str(midi_path))
                    note_count = sum(len(i.notes) for i in pm.instruments)
                    score = converter.parse(str(midi_path))
                    xml_path = Path(work) / "transcription.musicxml"
                    score.write("musicxml", fp=str(xml_path))
                    xml_bytes = xml_path.read_bytes()
                    mxl_bytes = None
                    try:
                        mxl_path = Path(work) / "transcription.mxl"
                        score.write("mxl", fp=str(mxl_path))
                        mxl_bytes = mxl_path.read_bytes()
                    except Exception:
                        pass
                st.session_state["results"] = {
                    "midi": midi_bytes, "xml": xml_bytes, "mxl": mxl_bytes, "notes": note_count
                }
            except Exception as ex:
                st.error(f"Transcription failed: {ex}")
                st.warning("If MP3/M4A decoding fails, install FFmpeg or use a WAV file. Some model dependencies need compatible Python versions.")
if "results" in st.session_state:
    r = st.session_state["results"]
    st.success(f"Transcription generated: {r['notes']} detected notes. Review by listening before importing into Artie.")
    st.download_button("Download MIDI (.mid)", r["midi"], file_name="transcription.mid", mime="audio/midi")
    st.download_button("Download MusicXML (.musicxml)", r["xml"], file_name="transcription.musicxml", mime="application/vnd.recordare.musicxml+xml")
    st.download_button("Download XML (.xml)", r["xml"], file_name="transcription.xml", mime="application/xml")
    if r["mxl"]:
        st.download_button("Download MXL (.mxl)", r["mxl"], file_name="transcription.mxl", mime="application/vnd.recordare.musicxml")
st.caption("Transcription runs on your computer. This version uses Spotify Basic Pitch and is not multi-instrument separation software.")
