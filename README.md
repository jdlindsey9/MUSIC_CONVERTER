# MUSIC_CONVERTER

Local audio transcription with two distinct piano workflows and an isolated-instrument baseline. All processing runs on your computer.

## Windows: install or update

1. Install **64-bit Python 3.11** with the `py` launcher.
2. Extract the repository ZIP into a writable folder. To update an existing installation, close its command window, copy the new files into the existing app folder and replace matching files. Keep `.venv` and `outputs`.
3. Double-click **START_WINDOWS.bat**. It installs pinned dependencies and opens http://localhost:8501. Leave the command window open. If Streamlit asks for an email, leave it blank and press Enter.
4. For piano isolation, close the app and run **INSTALL_PIANO_WINDOWS.bat** once. Choose **G** for an NVIDIA GPU (including RTX 4070 Super), or **C** for CPU. Then run START_WINDOWS.bat again. The optional installer adds PyTorch, torchaudio and Demucs; first separation downloads model weights from `dl.fbaipublicfiles.com`.

Piano arrangement and the baseline work without the optional installer. No paid API is required. CUDA requires an appropriate NVIDIA driver; choose CPU if CUDA is unavailable. Native GPU inference has not been tested in the cloud environment.

## Choose a mode

| Mode | What it does | Limitations |
|---|---|---|
| **Piano part only (experimental isolation)** | Runs Demucs `htdemucs_6s`, selects its piano stem, then runs Basic Pitch on that stem. Provides isolated piano audio and MIDI. | Separation may leak other instruments or lose piano. Upstream explicitly warns that its piano source is weak. It cannot guarantee an exact piano-only part. Model inference remains unverified here because the cloud blocked the weight host. |
| **Whole song → piano arrangement** | Detects notes in the whole recording, then creates left/right-hand piano tracks with fewer simultaneous notes. Keeps a low bass voice and upper melody candidate, filling remaining slots with strong sustained harmony. | Generated heuristic reduction, not an exact transcription or learned musical arrangement. Errors in source note detection remain possible. Highest-note selection can mistake a harmonic for melody. No promise of human-level arranging or full playability. |
| **Already isolated instrument (baseline)** | Runs Basic Pitch directly, preserving its detected performance. | Does not identify or separate instruments. Use for a solo instrument or a stem already isolated elsewhere. |

The arrangement slider limits simultaneous notes to 2–6 (default 4). Notes outside MIDI 36–96, notes shorter than 120 ms and drum tracks are excluded from the arrangement; duplicate simultaneous pitches are suppressed. Each hand stays within a 12-semitone span at any instant. This does not constrain hand movement between notes. Basic Pitch's original output remains downloadable separately; the arrangement never overwrites it. The isolated baseline mode avoids this reduction.

## Review and download

Upload MP3/WAV/FLAC/M4A/OGG/AAC/AIFF/WMA (100 MB, 20 minutes maximum), then click **Transcribe recording**. Review the piano roll, play the original recording, isolated stem if available, and synthesized notes. Synthetic playback is simple tones, not a piano soundfont. The players are independent, not synchronized.

Edit pitch, start/end seconds and velocity in the table, then apply edits. New notes must use an existing track index. Score quantization changes MusicXML only; MIDI retains performance timing. Basic Pitch's default 120 BPM is a notation assumption, not estimated tempo. Pedal detection and chord labels are not implemented.

Download `.mid`/`.midi`, `.musicxml`/`.xml`, or compressed `.mxl`. Exports are reopened before download. If score export fails, MIDI is still available. Files are also saved automatically under **outputs**, in a new timestamped folder displayed in the app. Edits create another folder. These folders persist until you delete them.

If the browser says a download cannot be reached, use **Save MIDI directly** or open the displayed folder in File Explorer and use `transcription.mid`. Inline audio and the direct MIDI link do not depend on Streamlit's `/media` URLs. The ordinary download buttons remain available and no longer rerun the app. The precise cause of the reported Windows media/download failure has not been established.

Results remain in browser-session memory until a source/mode change or restart; saved output folders persist. Generated source recordings/stems are local and are never added to Git. Artie import and subjective musical quality require user review.

## Development

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock.txt
pip install "pytest>=8,<9"
python -m pytest -q
PYTHONPATH=. python tests/real_transcription.py
python -m streamlit run app.py
```

Windows uses `requirements-windows.lock.txt` rather than the Linux lock. Optional separation dependencies are in `requirements-piano.txt`; select CPU or CUDA PyTorch wheels before installing it. Linux/Windows CI tests the base application; separator tests are skipped if optional packages are absent.

Browser tests require Playwright and Chromium. Run `PYTHONPATH=. python tests/browser_smoke.py` against the server; `APP_URL` and `CHROMIUM_PATH` override defaults. Windows cmd syntax: `set PYTHONPATH=.` and `set CHROMIUM_PATH=...`, then run the script normally.

Regenerate platform locks with `uv pip compile requirements.txt --python-version 3.11 --python-platform linux -o requirements.lock.txt` (substitute `windows` and the Windows filename). The setuptools cap fixes resampy's use of `pkg_resources`.

See [validation report](docs/TEST_REPORT.md) and [model assessment](docs/MODELS.md). Specialized piano transcription (Transkun), learned arrangement, robust instrument identification, tempo estimation and representative accuracy benchmarks remain future work.
