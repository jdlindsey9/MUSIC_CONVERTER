# Fix imported MIDI score export and expose score-recognition timing errors

A user-supplied MIDI failed MusicXML export because the importer treated precise MIDI timing as already engraved notation, bypassing score quantization. MIDI performance timing is now retained while notation is reconstructed using the selected quantization; native MusicXML keeps its supported notation.

The same test set revealed missing tempo and overfull measures in PDF recognition. Imports now warn about those cases and support an explicit starting-tempo override. Reference-note comparisons flag timing discrepancies, and a local benchmark CLI records reproducible diagnostics without claiming aligned ground truth.

Validation: 40 tests, successful export/reopening of the user's 1,003-note MIDI, full-recording Basic Pitch/Transkun inference, and eight-page Audiveris recognition/export. Timing/instrument scope differs between the supplied recording and reference, so raw F1 is not claimed as model accuracy. See docs/COLD_BENCHMARK.md. User music/score files are excluded from Git.
