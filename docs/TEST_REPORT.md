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

# Piano modes and media update — October 27, 2026 (Chicago)

User-provided MusicXML inspection found a single Electric Piano part and a fixed 120 BPM notation tempo. Its note entries include rests/tied notation; they are not separate instrument detections. The submitted MP3 decoded to 297.665 seconds. No claim of auditory listening or instrument identification is made from metadata alone.

## Implemented

- Experimental existing-piano workflow: stereo 44.1 kHz decode → Demucs htdemucs_6s piano stem → Basic Pitch → original stem audio plus MIDI/score. Explicit CPU/CUDA/auto selection and optional Windows GPU/CPU installer. No fallback from failed isolation to the unseparated mix.
- Generated whole-song reduction: bass/upper melody candidates and strong harmony, 2–6 simultaneous notes, no duplicate pitches per hand, octave span per hand, two named acoustic-piano tracks. This is a deterministic heuristic, not a trained arrangement model; it can retain transcription errors or choose a harmonic as melody.
- Inline audio, a direct MIDI data-link and automatic local output folders/ZIP archives. These avoid depending exclusively on Streamlit media endpoints. Downloads no longer trigger reruns. Score failures leave MIDI available. Changing source/mode/density clears stale results. Piano roll now uses one trace per track.
- Pinned Streamlit 1.50.0 after reproducing an ASGI response error with 1.60.0 (`Expected ASGI message http.response.start, but got http.response.body`) during browser testing. This is evidence of a media-serving problem here, not proof of the precise failure on the user's PC. Base locks regenerated for both platforms.

## Executed validation

- Real CPU Basic Pitch inference on the entire submitted MP3: 2,275 notes, one track, peak overlap 11. Generated four-note reduction: 2,175 note events, two tracks, peak overlap 4. Inference/reduction/export took 39.25 seconds in this run. MIDI, MusicXML and MXL reopened. These are counts and resource observations, **not measured musical accuracy**; no ground-truth MIDI was supplied.
- 22 automated tests pass with optional CPU Demucs installed. Includes arrangement density/hand-span invariants through overlapping note changes, duplicate suppression, drum exclusion, original preservation, two-track export, durable ZIP/file output, separator channel selection, failed-weight handling, UI mode routing/stale-result clearing, and score-failure MIDI retention. Separator tests use mocked model outputs; they do not establish actual separation quality.
- Actual Chromium upload → arrangement inference → valid MXL and MIDI download. Inline audio metadata loads and direct MIDI download works with `/media/` routes explicitly blocked. Upload replacement and corrupt-audio failure tested. Streamlit 1.50.0.
- Optional Demucs 4.0.1 + CPU torch/torchaudio 2.5.1 installed successfully; dependency check passed. Actual `get_model('htdemucs_6s')` attempted and blocked by cloud network policy at `dl.fbaipublicfiles.com` (403). No alternative host or proxy bypass attempted.

## Remaining limitations

Piano-isolation model inference and musical quality on the user's song remain **unverified** because weights could not be retrieved here. Windows optional installer, CUDA/RTX behavior, native browser media repair and Artie import still need verification on the user's computer. The supplied screenshots do establish that the earlier baseline installed and ran on Windows. The generated reduction is a first draft and is not validated as a musical arrangement by listening. This work does not add Transkun, trained multi-instrument transcription, pedal detection, beat tracking, or synchronized playback.

User recording, original MusicXML and generated musical files are not committed to Git. Files generated for inspection are under the ignored `outputs` folder.
