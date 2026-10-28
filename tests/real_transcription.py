"""Opt-in real model smoke benchmark; synthetic audio is not a piano corpus."""
import io
import json
import time
from pathlib import Path
import numpy as np
import pretty_midi
import mir_eval
from music_converter.pipeline import decode_audio, transcribe, export_files, preview_wav, note_rows

midi = pretty_midi.PrettyMIDI()
inst = pretty_midi.Instrument(0)
for i, pitch in enumerate([60, 64, 67, 72]):
    inst.notes.append(pretty_midi.Note(100, pitch, 0.5 + i, 1.25 + i))
midi.instruments.append(inst)
audio, rate = decode_audio(preview_wav(midi))
start = time.perf_counter()
result = transcribe(audio, rate)
files = export_files(result)
ref, est = note_rows(midi), sorted(note_rows(result), key=lambda n: n['start'])
def arrays(rows):
    return np.array([[r['start'], r['end']] for r in rows]), pretty_midi.note_number_to_hz(np.array([r['pitch'] for r in rows]))
ri, rp = arrays(ref)
ei, ep = arrays(est)
p, r, f, _ = mir_eval.transcription.precision_recall_f1_overlap(ri, rp, ei, ep, offset_ratio=None)
report = dict(fixture='Four synthesized sine notes; not representative of piano recordings', seconds=round(time.perf_counter()-start, 2), reference_notes=len(ref), detected_notes=len(est), onset_precision=p, onset_recall=r, onset_f1=f, detected=est, exports=list(files))
Path('docs/smoke-result.json').write_text(json.dumps(report, indent=2, default=lambda x: x.item()))
print(json.dumps(report, indent=2, default=lambda x: x.item()))
