"""Reproduce a local audio/reference MIDI comparison without committing source files.

Run from the project root: python -m scripts.benchmark_audio --help
Metrics are unaligned diagnostics unless independently verified as the same
performance and start time. Comparing a piano score to a full mix also includes
out-of-scope instruments; do not interpret the result as isolated-piano accuracy.
"""
import argparse
import json
from pathlib import Path
import time
import pretty_midi
from music_converter.pipeline import decode_audio, transcribe, export_files, midi_bytes, note_rows
from music_converter.piano_model import transcribe_piano
from music_converter.evaluation import compare_notes


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audio',required=True,type=Path)
    parser.add_argument('--reference',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--models',nargs='+',choices=['basic-pitch','transkun'],default=['basic-pitch','transkun'])
    parser.add_argument('--device',choices=['auto','cpu','cuda'],default='cpu')
    args=parser.parse_args()
    audio,rate=decode_audio(args.audio.read_bytes())
    reference=pretty_midi.PrettyMIDI(str(args.reference))
    args.output.mkdir(parents=True,exist_ok=True)
    report={'audio_seconds':len(audio)/rate,'reference_seconds':reference.get_end_time(),
            'interpretation':'Unaligned diagnostic only; performance correspondence and instrument scope require verification.'}
    for model in args.models:
        started=time.perf_counter()
        result=transcribe(audio,rate) if model=='basic-pitch' else transcribe_piano(audio,rate,args.device)
        (args.output/(model+'.mid')).write_bytes(midi_bytes(result))
        stats={'notes':len(note_rows(result)),'inference_seconds':round(time.perf_counter()-started,2),
               'unaligned_diagnostic':compare_notes(reference,result)}
        try:
            exports=export_files(result)
            for ext,data in exports.items():
                (args.output/(model+'.'+ext)).write_bytes(data)
            stats['exports_reopened']=list(exports)
        except Exception as exc:
            stats['score_export_error']=str(exc)
        report[model]=stats
        (args.output/'report.json').write_text(json.dumps(report,indent=2))
        print(model,json.dumps(stats),flush=True)


if __name__=='__main__':
    main()
