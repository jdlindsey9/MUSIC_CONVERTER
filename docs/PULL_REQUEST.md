# Add piano-specialized detection, sheet-music import and accuracy measurement

Users can now select Transkun V2 for piano note detection and import sheet music directly. MusicXML/MXL preserves supported notation instead of passing through audio inference; PDFs/images use local Audiveris, with an explicit play-once option for incomplete repeat markings. MIDI import, review, editing and validated exports share the existing result workflow.

The optional Windows model installer handles Transkun's training-only ncls dependency through a metadata-only compatibility wheel; source and checkpoint bytes remain unchanged. A separate script installs official Audiveris. Thorough Demucs settings expose a slower ensemble option, while reference MIDI comparisons measure actual note precision/recall/F1 without automatic alignment or tuning.

Validation: 36 tests; real Transkun inference on 20 seconds of submitted audio; real Audiveris PDF recognition (277 notes, two parts); Chromium PDF-to-MIDI/MXL downloads and audio workflow regression. Windows/CUDA, Artie, image OMR and accuracy against real ground truth remain unverified. Existing bleed is not claimed solved: stronger separation candidates are documented, with gated-weight/resource limitations. See docs/TEST_REPORT.md.
