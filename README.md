# MUSIC_CONVERTER

A local Streamlit application for audio → editable MIDI → MusicXML. Phase 1 uses Spotify Basic Pitch for isolated instruments. It is a tested baseline, not yet the high-accuracy piano or multi-instrument system.

## Windows installation

1. Install **64-bit Python 3.11**, including the Windows `py` launcher.
2. Extract/clone this repository into a writable folder.
3. Double-click **START_WINDOWS.bat**. The first run installs the pinned dependencies (including a large TensorFlow download) and opens the browser at http://localhost:8501. Internet is required for installation; inference runs locally with packaged Basic Pitch weights. FFmpeg is bundled through imageio-ffmpeg.
4. Upload MP3, WAV, FLAC, M4A, OGG or another supported format; choose thresholds and click **Transcribe recording**.
5. Listen to both players, inspect the piano roll and edit the note table. Click **Apply edits and rebuild exports** to save corrections. Times are seconds; pitches and velocities are MIDI values. Added notes must use an existing track index.
6. Download `.mid`/`.midi`, `.musicxml`/`.xml` or `.mxl`. Original detected MIDI is separately available after edits. Results live in browser-session memory; download before closing/reloading.

If upgrading an old installation, remove its `.venv` directory before launching. Setup stops on dependency failures and leaves the error visible. Native Windows execution and automatic browser launch remain unverified in the Linux development environment. This baseline uses CPU inference on native Windows; CUDA integration for specialized piano models is future work.

## Behavior and limits

- Decode by file content into mono 22.05 kHz WAV using bundled FFmpeg. Limit: 100 MB and 20 minutes. Silent, empty, oversized and invalid input is rejected.
- Original preview uses the uploaded recording; generated playback is synthesized audio, not realistic piano. Compare with independent players; synchronized A/B playback is not implemented.
- MIDI preserves detected performance timing. Score quantization is optional and never rewrites MIDI. Basic Pitch's default tempo is a notation assumption, **not measured song tempo**. Beat/tempo estimation and chord labels are not implemented.
- MusicXML encodes chords/parts via music21, and MXL is a real compressed MusicXML archive. Every export is reopened before download. `.mid` and `.midi` are equivalent valid MIDI; `.xml` and `.musicxml` are equivalent valid MusicXML.
- Exact score notation may become complex or fail for unusual unquantized durations. Export errors are shown rather than silently omitting MXL. Raw original timing remains in the model MIDI; no tempo-map inference, reliable pedal detection or instrument identification is claimed.
- Minimum duration filtering can be disabled with zero. Onset/frame thresholds control model activations, not probabilities of correctness. No extra heuristic cleanup silently changes the detected performance.
- Full Song and Piano Arrangement modes are **not implemented**. Do not interpret mixed-audio output as separated instruments. Artie by ArtMaster import is **unverified**.

## Development and tests

```bash
python3.11 -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.lock.txt
pip install -r requirements-dev.txt
python -m pytest -q
PYTHONPATH=. python tests/real_transcription.py
python -m streamlit run app.py
```

The smoke script runs real inference on four synthesized notes and writes `docs/smoke-result.json`. It is not a representative piano benchmark. On Windows, set `PYTHONPATH=.` in cmd before running the script. Browser automation additionally requires `pip install playwright` and an installed Chromium; set `CHROMIUM_PATH` to its executable and run `tests/browser_smoke.py` against the running app.

`requirements.txt` defines supported dependency ranges; `requirements.lock.txt` pins the Linux runtime; `requirements-windows.lock.txt` separately resolves Windows wheels, including TensorFlow Intel and its older GCS dependency, for Python 3.11. Regenerate with `uv pip compile requirements.txt --python-version 3.11 --python-platform linux -o requirements.lock.txt` (use `--python-platform windows` and the Windows filename for Windows). The setuptools cap fixes resampy's use of the removed `pkg_resources` API.

See [test report](docs/TEST_REPORT.md) and [model assessment / next phases](docs/MODELS.md).
