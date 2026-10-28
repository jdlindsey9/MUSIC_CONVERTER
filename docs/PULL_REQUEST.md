# Repair and validate the local transcription pipeline

The prototype could show results from the wrong upload and silently omit MXL exports. This change decodes audio through bundled FFmpeg, runs Basic Pitch, validates MIDI and score exports, and clears stale results. It adds piano-roll review, synthesized playback, editable note tables and a separately downloadable original performance. MIDI timing is independent of optional score quantization.

The Windows launcher now stops on installation errors and uses Python 3.11 with a separately resolved Windows lock. A setuptools compatibility constraint fixes Basic Pitch's resampy import. Automated Linux/Windows checks and model assessment notes document remaining phases.

Validation: 14 passing tests; real CPU inference on a four-note synthetic fixture; Chromium upload/inference/MXL download and corrupt-upload flow; Streamlit health check; dependency checks. Native Windows, GPU, Artie import and real piano accuracy remain unverified. Full-song separation and piano arrangements are future phases. See docs/TEST_REPORT.md.
