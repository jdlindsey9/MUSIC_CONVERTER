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

## Follow-up implementation

The two piano workflows now exist as experimental isolation and heuristic arrangement. The Demucs upstream README was inspected directly: https://github.com/facebookresearch/demucs (six-source model section). It explicitly says the piano stem has substantial bleed/artifacts. Therefore it is labelled experimental and its isolated audio is exposed for listening before trusting the transcription. It is not described as the best available piano separator.

PyTorch/torchaudio 2.5.1 and Demucs 4.0.1 are an optional dependency group, with NVIDIA CUDA 12.1 and CPU wheel choices. No measured VRAM or Windows GPU speed is available. The model weight host was blocked in the cloud, so actual separation quality is not claimed. A newer piano-specific separator and Transkun evaluation remain the next accuracy tasks.

The generated arrangement reduces Basic Pitch's output from the full mix. It uses no invented instrument labels, and its hand labels describe generated piano roles. It is not equivalent to reconstructing all source instrument tracks or identifying true melody/chord structure.

## Piano detector and separation research follow-up

Sources inspected directly:

- [Transkun V2](https://github.com/Yujia-Yan/Transkun) and PyPI `transkun==2.0.1`: packaged 2.0 checkpoint/config, piano-specific note/velocity/pedal inference and CPU/CUDA support. Integrated and executed on a 20-second real-audio excerpt. Upstream MAESTRO results are not measurements on the user's recording. The default checkpoint uses a no-pedal-extension note convention; match this when evaluating offsets.
- [SAM Audio](https://github.com/facebookresearch/sam-audio): targets sounds using text, visual or temporal prompts. This is a candidate for targeting piano directly rather than relying on Demucs's weak sixth stem. Upstream requires gated checkpoint access/authentication and uses the SAM License. It recommends CUDA; span prediction and reranking increase memory/latency. No weights retrieved, no piano-quality measurement and no verified fit on the user's 12 GB RTX 4070 Super. This is a research candidate, not an installed or proven superior backend. No credentials or gated access were requested automatically.
- [Music Source Separation Training](https://github.com/ZFTurbo/Music-Source-Separation-Training) and [audio-separator](https://github.com/nomadkaraoke/python-audio-separator): BS-RoFormer/Mel-Band RoFormer inference/training ecosystems support strong separation architectures. The curated tables inspected here did not establish an evaluated piano-specific checkpoint superior to Demucs. Vocal/instrumental checkpoints are not piano-isolation models. Investigate a properly licensed piano-trained checkpoint with paired stem benchmarks before integration; do not claim better piano performance from a vocal SDR result.
- [Audiveris 5.11.0](https://github.com/Audiveris/audiveris/releases/tag/5.11.0): local optical music recognition with Windows/Linux/macOS installers and MusicXML export. Actual PDF recognition and browser downloads were tested. It preserves a different kind of information from audio inference and can make symbol/voice/repeat errors.

Current optimization is explicit: optional Transkun for piano, a higher-cost Demucs ensemble setting, native score import to avoid audio recognition when score data exists, and actual note metrics for a future ground-truth corpus. No statement of 100% accuracy or measured reduction in bleed is justified yet. Separation improvement, note transcription improvement and score recognition quality must be evaluated separately.
