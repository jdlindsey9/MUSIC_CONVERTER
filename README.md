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

## Piano-specialized detection and sheet music

Update the app files, then rerun **INSTALL_PIANO_WINDOWS.bat** (G for NVIDIA). In Audio recording mode, choose **Transkun V2 (piano)** under Note detector. Use it on an isolated piano recording or the experimental piano stem. Basic Pitch stays available for comparisons; whole-song arrangements still use Basic Pitch because Transkun is trained for piano. Transkun's packaged V2 model includes pedal/control detection, but their accuracy has not been measured here. It cannot remove bleed from the separator. The Basic Pitch threshold controls are disabled when Transkun is selected.

**Thorough piano separation** uses five shifted Demucs passes and 50% overlap instead of one pass/25%. It costs more time and may reduce boundary/shift artifacts; it is not a new separator or a guarantee of less bleed. CPU/CUDA/auto applies to both separation and Transkun. A 20-second real-audio excerpt was processed on CPU; native Windows/CUDA performance still needs testing.

Select **Sheet music / MIDI** to upload:

- **MusicXML / MXL / XML:** preferred for written music. Imports notes and supported notation directly without audio inference. Supported tempo, meter and repeats are retained in score exports until you apply note edits; editing rebuilds notation from MIDI and can lose engraving detail.
- **MIDI / MID:** imports performance notes directly.
- **PDF / PNG / JPEG / TIFF:** uses local Audiveris optical music recognition. Run **INSTALL_SHEET_MUSIC_WINDOWS.bat** once and complete the official Audiveris installer. Enter the path to `Audiveris.exe` if automatic detection fails. This installer downloads official Audiveris 5.11.0 with its Java runtime. Internet is required for installation; recognition is local.

Click **Import score**, review/play the result and export. Optical recognition is imperfect: check accidentals, voices, rhythm and missing notes. **Play written measures once** is enabled by default; this ignores repeats in MIDI playback but preserves repeat symbols in MusicXML. Disable it for complete scores with valid repeat structure. Incomplete excerpts may not support expanded-repeat playback. Scores producing over 20 minutes of playback are rejected; split long scores into sections. The application supports one combined exported score per PDF; multi-movement outputs must be reviewed/exported in Audiveris first.

The Transkun Windows installer creates version `2.0.1+musicconverter.1` from the official 2.0.1 wheel. It changes only package metadata: `ncls`, used by training-dataset indexing, becomes an optional `training` extra because it has no Windows wheel. Source code, model weights and licenses remain unchanged. Inference was tested with `ncls` imports blocked. This package is intended for inference; training tools still need the extra dependency.

## Measuring improvements

After conversion, expand **Measure note accuracy against a reference MIDI**. Upload known-correct MIDI from the **same performance with matching start time**, then click Compare notes. The JSON reports precision, recall, onset F1 and onset-plus-offset F1 using mir_eval. Onsets allow 50 ms; offsets allow the larger of 50 ms or 20% of reference duration. No automatic alignment or tuning is applied. MIDI from a different performance or different sustain-pedal conventions is not a valid direct comparison.

For the next benchmark, provide the mixed recording, its isolated piano stem from the same performance if available, and corresponding MIDI/MusicXML. A separately played piano cover is useful for musical review but not exact timing ground truth. Use several pieces, keeping some unused during tuning, to avoid overfitting one song. Audio waveform identity is not an appropriate target for synthesized MIDI with a different piano sound.

Reference comparisons now flag large start/end timing discrepancies; these can come from alignment problems, different performances or detection errors. The warnings do not automatically correct or excuse model errors. Use `python -m scripts.benchmark_audio --help` for reproducible local comparisons.

Sheet imports warn about missing numeric tempo and overfull measures. Use **Starting tempo BPM (0 = use score)** to supply a printed tempo missed by recognition; it applies to MusicXML/PDF/image scores, not imported performance MIDI. This changes only the initial tempo and does not repair rhythmic recognition errors. Fix overfull measures in Audiveris or a notation editor before relying on their playback. See the [Cold test report](docs/COLD_BENCHMARK.md) for an example.
