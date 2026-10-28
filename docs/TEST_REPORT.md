# Phase 1 validation report

Executed October 27, 2026 (America/Chicago), Linux x86_64, Python 3.11.17, CPU. No NVIDIA GPU available.

## Passed

- Installed runtime dependencies, then the pinned lock; `uv pip check`: all installed packages compatible. Basic Pitch 0.4.0, TensorFlow 2.15.0, music21 9.9.2, NumPy 1.26.4. Windows-specific dependencies resolved separately (not executed).
- `python -m pytest -q`: **14 passed**. Checks chord and two-track MIDI round trips (pitch and timing), quantized/unquantized MusicXML/XML/MXL parsing and part/pitch retention, real ZIP container, original preservation during edits, invalid edit rejection, silence/corrupt input, empty transcription rejection, preview generation, five actual audio codec conversions, Streamlit startup and upload state/error workflow. AppTest upload test injects bytes and mocks inference; browser test below uses real inference.
- Started Streamlit on localhost:8501; HTTP health endpoint returned `ok`.
- Headless system Chromium via Playwright: actual WAV upload → Basic Pitch inference → download valid MXL; replacing the upload removes old downloads; corrupt upload reports decode error. Browser runtime initially used TensorFlow 2.15.0.post1, before lock installation; locked TensorFlow 2.15.0 subsequently passed the model and unit tests.
- Real model smoke test: four synthetic sine notes, four detected notes, onset precision/recall/F1 **1.0**, using mir_eval defaults (50 ms onset tolerance, 50 cents pitch tolerance, offsets excluded). Latest run ~9.1 seconds including model import/load, inference and exports. Results in `smoke-result.json`. This tiny synthetic fixture establishes pipeline operation, **not piano-recording accuracy**.
- Bundled FFmpeg decoded WAV, MP3, FLAC, M4A and OGG generated from an audio fixture. MXL and MusicXML reopened successfully. MIDI performance timing retained within 3 ms in the round-trip fixture.
- `git diff --check` clean.

## Bugs found and fixed

- MXL compression reused and deleted the uncompressed XML path: use separate base filenames.
- New setuptools removed pkg_resources, breaking resampy during Basic Pitch import: constrain setuptools below 81.
- Changing uploads previously exposed stale results: clear results on source-content change and conversion retries.
- MXL failures were silently ignored: surface failures and validate outputs.
- Windows launcher continued after install errors: stop on failures and use platform-specific pinned dependencies. Windows TensorFlow requires tensorflow-intel and GCS 0.31.0; a Linux-resolved lock is insufficient.

## Unverified / incomplete

- Native Windows install, browser opening, RTX 4070 Super/CUDA, Artie import, real recorded piano benchmarks, long-song memory/runtime and subjective audio playback quality. Windows/Linux CI is added but its remote result is not claimed here.
- AAC, AIFF and WMA are offered by the uploader but were not exercised individually. Actual browser upload tested with WAV; other codecs tested at decoder boundary.
- No specialized solo-piano model, multi-instrument model/separation, arrangement engine, tempo estimation, pedal detection, chord labels or graphical note dragging. Editing uses a table. Playback comparison uses separate players.
- Playwright browser download was denied by network policy; the already-installed system Chromium successfully ran the browser test.

## Windows handoff and next phase

Install Python 3.11, run START_WINDOWS.bat, convert a short isolated piano recording, review notes, and import the downloaded MIDI and MXL into Artie. Note any rejected format or timing discrepancy. Next: benchmark Transkun V2 against this baseline with matched ground-truth and pedal conventions, then add CUDA support and multi-instrument work.
