# Add separate piano-isolation and generated-arrangement workflows

The baseline collapsed a mixed recording into one MIDI instrument, and media/download links failed on the user's Windows setup. The app now offers experimental Demucs piano-stem extraction before transcription, a separate whole-song piano reduction with two hand tracks and limited polyphony, and the original isolated-instrument baseline.

Results are saved locally as well as offered through download buttons, a direct MIDI link and embedded audio. MIDI stays available if score export fails. Streamlit is pinned to 1.50.0 after reproducing an ASGI response failure with 1.60.0. The optional Windows installer selects CPU or NVIDIA CUDA dependencies for separation.

Validation: 22 automated tests; Chromium upload, real inference and MIDI/MXL downloads, embedded audio/direct download with media routes blocked; real transcription and export of the user's 297.665-second recording. Its peak overlap was reduced from 11 notes to 4 across two generated piano tracks. Counts are not an accuracy benchmark.

Limitations: actual Demucs weights were blocked by cloud network policy, so piano-isolation inference is unverified. Its upstream piano stem has known bleed/artifact limitations. The arranger is a heuristic draft, not a learned model. Windows GPU and Artie tests remain outstanding. Uploaded and generated musical files are excluded from Git.
