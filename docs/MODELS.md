# Model assessment and next phases

Upstream sources inspected during implementation (October 27, 2026, Chicago date):

| System | Evidence and fit | Decision |
|---|---|---|
| [Spotify Basic Pitch](https://github.com/spotify/basic-pitch) | Lightweight polyphonic, instrument-agnostic model; documented Python 3.7–3.11 and Windows support. Packaged TF, TFLite, CoreML and ONNX models. Most suitable for isolated instruments; no source identification. | Phase 1 baseline. Actual CPU inference and exports tested. |
| [Transkun V2](https://github.com/Yujia-Yan/Transkun) | Piano-specialized; upstream CLI supports `--device cuda`. Default shipped checkpoint is V2 No Pedal Ext, whose note-duration convention differs from pedal-extended benchmark variants. Upstream publishes MAESTRO model-card results. | First Phase 2 candidate. Do not transfer published MAESTRO scores to this app or compare variants without matching pedal convention. Windows install, VRAM use, checkpoint availability and RTX performance need measurement. |
| [YourMT3+](https://github.com/mimbres/YourMT3) | Upstream links its 2024 paper, pre-release code and GPU demo for multi-task/multi-track transcription. More integration and checkpoint work than Basic Pitch. | Phase 3 investigation, not an implemented backend. No comparative accuracy measured here. |
| [Demucs](https://github.com/facebookresearch/demucs) | Candidate source-separation stage, not itself a note transcriber. Separation artifacts can harm downstream transcription. | Evaluate separated versus original audio; do not treat broad stems as exact instrument labels. |

Only the first three upstream READMEs were fetched and inspected here; Demucs remains a candidate for detailed review. No claim that this is an exhaustive survey or that a winner has been established. Exact GPU memory/resource requirements, Windows compatibility of specialized models, and redistribution licenses must be checked before bundling their weights.

Phase 1 delivered: decoding, baseline inference, validated exports, UI progress stages, original and synthesized playback, note-table editing, piano roll, Windows launcher, tests.

Phase 2 next: isolate Transkun dependencies, add explicit CPU/CUDA selection, retain pedal/controller events, and benchmark Basic Pitch versus Transkun on licensed piano audio with aligned ground truth. Report onset and onset/offset precision/recall/F1, velocity error, runtime, peak RAM/VRAM and checkpoint/version. Match pedal conventions and evaluate chords/repeated notes/quiet passages. No real piano corpus was supplied in this session.

Phase 3: evaluate YourMT3+ and source separation with instrument-labelled ground truth. Preserve track identities only when supported by model output.

Phase 4: implement a clearly labelled generated piano arrangement with hand assignment, playable ranges and melody/bass prioritization. Extend the current editor with graphical editing and synchronized A/B playback.

Phase 5: validate Windows and Artie imports with user recordings; benchmark and tune without claiming guaranteed transcription accuracy.
