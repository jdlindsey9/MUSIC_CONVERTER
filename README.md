# MUSIC_CONVERTER

A Windows-local Streamlit prototype that attempts to convert uploaded audio into MIDI, MusicXML and MXL for import into piano learning apps such as Artie.

## Run on Windows

1. Install 64-bit Python 3.10 from python.org, including the py launcher.
2. Download this GitHub repository as a ZIP, extract it, and double-click START_WINDOWS.bat.
3. Wait for packages to install. Open http://localhost:8501 if the browser doesn't open automatically.
4. Upload an audio file and click Transcribe audio; download exports if transcription succeeds.

## Current capabilities and limitations

- Upload MP3/WAV/FLAC/M4A/OGG; format decoding may require FFmpeg.
- Attempts transcription using Spotify Basic Pitch, which is most suitable for one isolated instrument.
- Exports MIDI, MusicXML, XML and optional MXL.
- Does **not** yet transcribe an entire mixed commercial song accurately or create a piano arrangement.
- **Unverified**: this application was syntax-checked, but the installation and real audio conversion have not been tested on Windows.
- Dependency compatibility can require troubleshooting. This is an early prototype, not a production release.

## Codex development instructions

Open this repository in VS Code with the Codex extension, or in Codex Cloud after its setup error is resolved. Prioritize testing the full workflow and Windows dependencies first, then consider solo-piano transcription, multi-instrument models, source separation, note editing, improved export validation, and benchmarks against ground-truth MIDI. Do not claim accuracy without measured testing.
