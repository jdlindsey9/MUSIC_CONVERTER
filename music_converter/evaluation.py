"""Ground-truth note metrics. No automatic alignment or test-set tuning."""
import numpy as np
import pretty_midi
import mir_eval


def compare_notes(reference, estimate):
    def arrays(midi):
        notes = sorted((n for inst in midi.instruments if not inst.is_drum for n in inst.notes), key=lambda n: (n.start, n.pitch))
        intervals = np.array([[n.start, n.end] for n in notes], dtype=float).reshape((-1, 2))
        pitches = pretty_midi.note_number_to_hz(np.array([n.pitch for n in notes], dtype=float))
        return intervals, pitches
    ref_i, ref_p = arrays(reference)
    est_i, est_p = arrays(estimate)
    if not len(ref_i):
        raise ValueError('Reference MIDI contains no pitched notes.')
    warnings = []
    if len(est_i):
        first_difference = float(est_i[:, 0].min() - ref_i[:, 0].min())
        end_difference = float(est_i[:, 1].max() - ref_i[:, 1].max())
        if abs(first_difference) > .25:
            warnings.append(f'First note differs by {first_difference:+.2f} seconds. Verify start alignment; missing/extra notes can also cause this.')
        if abs(end_difference) > max(2, .02 * ref_i[:, 1].max()):
            warnings.append(f'Last note differs by {end_difference:+.2f} seconds. Verify performance/tempo correspondence; detection errors can also cause this.')
    onset = mir_eval.transcription.precision_recall_f1_overlap(ref_i, ref_p, est_i, est_p, onset_tolerance=.05, offset_ratio=None)
    duration = mir_eval.transcription.precision_recall_f1_overlap(ref_i, ref_p, est_i, est_p, onset_tolerance=.05, offset_ratio=.2)
    return dict(timing_warnings=warnings, reference_notes=len(ref_i), detected_notes=len(est_i),
                onset_precision=float(onset[0]), onset_recall=float(onset[1]), onset_f1=float(onset[2]),
                onset_offset_f1=float(duration[2]), onset_tolerance_ms=50,
                offset_tolerance='max(50 ms, 20% of reference duration)',
                alignment='No time alignment applied. Use the same performance, start time and pedal convention.')
