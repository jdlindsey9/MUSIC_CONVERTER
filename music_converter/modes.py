"""Distinct source extraction and generated-arrangement workflows."""
from __future__ import annotations

import copy
import numpy as np
import pretty_midi

PIANO = 'Piano part only (experimental isolation)'
ARRANGEMENT = 'Whole song → piano arrangement'
BASELINE = 'Already isolated instrument (baseline)'


def separate_piano(audio, rate, device='auto'):
    """Demucs six-source model has an actual piano target; never substitute 'other'."""
    try:
        import torch
        import torchaudio.functional as AF
        from demucs.pretrained import get_model
        from demucs.apply import apply_model
    except ImportError as exc:
        raise RuntimeError('Piano isolation needs the optional models. Run INSTALL_PIANO_WINDOWS.bat, then restart the app.') from exc
    if device not in ('auto', 'cpu', 'cuda'):
        raise ValueError('Choose auto, cpu or cuda.')
    device = ('cuda' if torch.cuda.is_available() else 'cpu') if device == 'auto' else device
    if device == 'cuda' and not torch.cuda.is_available():
        raise RuntimeError('CUDA is unavailable. Choose CPU or install CUDA models with INSTALL_PIANO_WINDOWS.bat.')
    try:
        model = get_model('htdemucs_6s')
    except Exception as exc:
        raise RuntimeError('Could not load Demucs piano weights. The first run needs access to dl.fbaipublicfiles.com. No unseparated mix was used as piano.') from exc
    model.eval()
    wave = np.asarray(audio, dtype=np.float32)
    if wave.ndim == 1:
        wave = np.column_stack([wave, wave])
    wave = torch.from_numpy(wave.T.copy())
    if rate != model.samplerate:
        wave = AF.resample(wave, rate, model.samplerate)
    ref = wave.mean(0)
    mean, std = ref.mean(), ref.std()
    if not torch.isfinite(std) or std < 1e-6:
        raise ValueError('Audio is silent or too quiet for source separation.')
    with torch.inference_mode():
        sources = apply_model(model, ((wave-mean)/std)[None], device=device,
                              shifts=1, split=True, overlap=0.25, progress=False)[0]
    piano = (sources[model.sources.index('piano')].cpu() * std + mean).T.numpy()
    if not np.isfinite(piano).all() or np.max(np.abs(piano)) < 1e-6:
        raise ValueError('The separator did not return audible piano. Try a different recording or an isolated piano stem.')
    return piano, model.samplerate


def arrange_piano(midi, max_notes=4, split_pitch=60, min_duration=.12):
    """Deterministic reduction, not instrument recognition or a learned arranger.

    At every note boundary, reserve an upper melody and a lower bass and fill
    remaining slots with strong sustained harmony. Each hand spans <= 12 semitones.
    Selected intervals are merged, with exact source note boundaries retained.
    """
    if not 2 <= max_notes <= 6:
        raise ValueError('Arrangement density must be between 2 and 6 notes.')
    events = {}
    notes = []
    for inst in midi.instruments:
        if inst.is_drum:
            continue
        for n in inst.notes:
            if 36 <= n.pitch <= 96 and n.end - n.start >= min_duration:
                idx = len(notes)
                notes.append(n)
                events.setdefault(n.start, [[], []])[1].append(idx)
                events.setdefault(n.end, [[], []])[0].append(idx)
    out = copy.deepcopy(midi)
    out.instruments = [pretty_midi.Instrument(0, name='Left hand - generated'),
                       pretty_midi.Instrument(0, name='Right hand - generated')]
    active, sounding = set(), {}
    right_limit = (max_notes + 1)//2
    left_limit = max_notes//2
    for time in sorted(events):
        ended, started = events[time]
        active.difference_update(ended)
        active.update(started)
        selected = {}
        for hand, pool, limit in (
            (0, [i for i in active if notes[i].pitch < split_pitch], left_limit),
            (1, [i for i in active if notes[i].pitch >= split_pitch], right_limit),
        ):
            if not pool:
                continue
            # Outer voices preserve bass and melody; inner voices favor velocity/duration.
            pool.sort(key=lambda i: (notes[i].pitch * (1 if hand == 0 else -1), -notes[i].velocity, i))
            anchor = pool[0]
            chosen = [anchor]
            pitches = {notes[anchor].pitch}
            for i in sorted(pool[1:], key=lambda i: (-notes[i].velocity, -(notes[i].end-notes[i].start), i)):
                if len(chosen) >= limit:
                    break
                if notes[i].pitch not in pitches and abs(notes[i].pitch - notes[anchor].pitch) <= 12:
                    chosen.append(i)
                    pitches.add(notes[i].pitch)
            selected.update({i: hand for i in chosen})
        for i in list(sounding):
            if i not in selected:
                hand, start = sounding.pop(i)
                if time > start:
                    n = notes[i]
                    out.instruments[hand].notes.append(pretty_midi.Note(n.velocity, n.pitch, start, time))
        for i, hand in selected.items():
            sounding.setdefault(i, (hand, time))
    for inst in out.instruments:
        inst.notes.sort(key=lambda n: (n.start, n.pitch))
    return out
