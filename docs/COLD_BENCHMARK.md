# Cold: user-supplied test set

User supplied an MP3, a two-track MIDI, and an eight-page PDF of Cold by Jorge Mendez. These files and generated musical outputs are **not committed**. Aggregate observations only are recorded here. Runs used Linux CPU with four OpenMP threads for Transkun; PDF recognition ran concurrently with two Java processors. Times are observations of this run, not controlled performance comparisons or Windows/GPU predictions.

## Source correspondence

- MP3 container duration: 296.856 seconds (about 4:57); mixed piano/violin recording according to its supplied filename. Source separation was not run because the model weight host remains inaccessible here.
- MIDI: 1,003 notes, two acoustic-piano program-0 tracks containing 864 and 139 notes; duration 306.124 seconds. Tempo changes from approximately 70 to 75 BPM. Track names are empty. pretty_midi warns about signature metadata outside the conductor track; tempo events were inspected and are on track 0.
- PDF: eight pages, arranged by Tiger Kong, with labelled violin, violoncello and piano staves. The opening printed tempo is quarter-note = 60.
- Basic Pitch's opening detected G4 pattern occurs around 11.6 seconds; the MIDI begins its G4 pattern at time zero. Durations and tempo also differ. Correspondence to an identical recorded performance is **not established**. Do not treat raw MP3/MIDI onset F1 as a model accuracy score.

## Completed tests

| Path | Observed output | Validation |
|---|---|---|
| Direct MIDI import | 1,003 notes retained | MIDI, MIDI alias, MusicXML, XML alias and MXL generated and reopened after fixing import/export handling |
| Basic Pitch on entire mixed MP3 | 2,408 notes; 16.79 seconds inference | All five export formats reopened |
| Transkun on entire mixed MP3 | 1,334 notes; 207.68 seconds inference | All five export formats reopened |
| Audiveris 5.11.0 on entire PDF | 1,298 notes across four MIDI tracks; 1,001 piano notes | All five export formats reopened; recognition contains important errors described below |

Neither audio run isolated piano first. Transkun is piano-specific but is being tested on a mix here; note counts alone cannot identify which notes are correct. No parameters were tuned to this song and no model weights were changed.

For reproducibility, unaligned audio diagnostics were computed with 50 ms onset tolerance: Basic Pitch precision 0.0469 / recall 0.1127 / onset F1 0.0663; Transkun precision 0.0682 / recall 0.0907 / onset F1 0.0779. These low numbers combine mismatched timing, potentially different arrangements, and extra source instruments with model errors. **They do not establish that either model is 6–8% accurate, nor that Transkun is more accurate.**

## PDF recognition findings

Audiveris labelled the two string parts as “Voice”, retained two piano tracks with 864 and 137 notes, missed the printed numeric tempo and defaulted playback to 120 BPM (192.125 seconds). It produced overfull piano measures: measure 27 with 8.25 quarter-note beats in 4/4, and measure 28 with 4.25 beats in 4/4. Later note timing is consequently shifted.

Comparing ordered pitches in the right-hand tracks gives 862 matching pitches out of 864 positions. This is a pitch-sequence diagnostic only, **not 99.8% overall transcription accuracy**. The left-hand note counts differ, and rhythm and tempo contain errors. Comparing piano note onsets in quarter-note beats without fitting any alignment gives precision 0.2617, recall 0.2612, F1 0.2615 (0.05-quarter-note tolerance). The low onset result shows why pitch matches alone are insufficient. MIDI durations use performed articulation, so exact durations are not a pure notation reference either.

## Application fixes driven by this test set

1. MIDI was incorrectly treated as native engraved notation, bypassing the user's score quantization setting. This generated unsupported 2048th durations and caused MusicXML export to fail. MIDI now retains its exact performance timing while score export reconstructs notation using the selected quantization. Native MusicXML still preserves supported original notation.
2. Sheet imports now warn when no numeric tempo was recognized and when measures contain more beats than their time signature allows. A starting-tempo override lets users enter the printed tempo; it does not fix rhythm recognition or later tempo changes. No guess was made about the correct performance tempo.
3. Reference comparisons warn about large first/last-note timing differences while retaining the raw diagnostic metrics. A reproducible CLI is included at `scripts/benchmark_audio.py`.

40 automated tests passed after these changes, including MIDI performance preservation, score quantization, tempo override, overfull-measure warnings and timing-mismatch warnings. Original recordings/score files are kept under attachments and outputs, outside version control.

## Recommended next use

For playing the purchased piano arrangement, import the supplied MIDI directly. It already contains only two acoustic-piano tracks and avoids audio separation and PDF recognition errors. For testing separation, obtain the isolated piano stem from the same recording if available. For a defensible note benchmark, align/verify the MIDI against that exact performance (including tempo and sustain conventions), then validate on other songs as well. Do not tune a universal model until one recording happens to match.

To repeat local model testing:

```bash
python -m scripts.benchmark_audio --audio path/to/recording.mp3 --reference path/to/reference.mid --output outputs/comparison --models basic-pitch transkun --device cpu
```

The script writes private output files and an aggregate report locally. It does not perform source separation, alignment or automatic parameter optimization.

Browser regression: the supplied MIDI was uploaded through the updated Sheet music / MIDI interface in Chromium. Both the generated MIDI and MXL downloaded successfully and their file headers were verified. This exercises the repaired import/export path with the actual regression file, not only a synthetic fixture.
