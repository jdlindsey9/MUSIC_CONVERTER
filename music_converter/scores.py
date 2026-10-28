"""Native symbolic import and optional Audiveris PDF/image recognition."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import zipfile
import io
import copy
import xml.etree.ElementTree as ET
import pretty_midi
from music21 import converter, bar, repeat, spanner, tempo

MAX_SIZE = 100 * 1024 * 1024


def find_audiveris(explicit=''):
    candidates = [explicit, os.environ.get('AUDIVERIS_PATH', ''), shutil.which('Audiveris') or '', shutil.which('audiveris') or '']
    for root in (os.environ.get('ProgramFiles', ''), os.environ.get('LOCALAPPDATA', '')):
        if root:
            candidates += [str(Path(root)/'Audiveris'/'Audiveris.exe'), str(Path(root)/'Audiveris'/'bin'/'Audiveris.exe')]
    for name in candidates:
        if name and Path(name).is_file():
            return str(Path(name).resolve())
    raise ValueError('Install Audiveris, then enter its executable path in Sheet music settings (for example C:\\Program Files\\Audiveris\\Audiveris.exe).')


def _xml_payload(data, suffix):
    if suffix == '.mxl':
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if sum(i.file_size for i in archive.infolist()) > MAX_SIZE:
                raise ValueError('Uncompressed score exceeds 100 MB.')
            container = ET.fromstring(archive.read('META-INF/container.xml'))
            rootfile = next((e.attrib.get('full-path') for e in container.iter() if e.tag.split('}')[-1] == 'rootfile'), None)
            if not rootfile:
                raise ValueError('MXL has no root score.')
            data = archive.read(rootfile)
    # Parse from memory. Never extract archive filenames or fetch referenced URLs.
    root = ET.fromstring(data)
    if root.tag.split('}')[-1] not in ('score-partwise', 'score-timewise'):
        raise ValueError('Expected a MusicXML score, not a generic XML document.')
    return ET.tostring(root, encoding='utf-8')


def import_score(data, filename, audiveris_path='', play_once=True, starting_tempo=None):
    if not data or len(data) > MAX_SIZE:
        raise ValueError('Choose a nonempty score smaller than 100 MB.')
    suffix = Path(filename).suffix.lower()
    supported = ('.musicxml', '.xml', '.mxl', '.mid', '.midi', '.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff')
    if suffix not in supported:
        raise ValueError('Use MusicXML, MXL, MIDI, PDF or a sheet-music image.')
    recognized = suffix in ('.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff')
    with tempfile.TemporaryDirectory() as work:
        root = Path(work)
        if recognized:
            executable = find_audiveris(audiveris_path)
            source = root / ('sheet' + suffix)
            source.write_bytes(data)
            output = root / 'recognized'
            try:
                run = subprocess.run([executable, '-batch', '-transcribe', '-export', '-output', str(output), '--', str(source)],
                                     capture_output=True, timeout=900)
            except subprocess.TimeoutExpired as exc:
                raise ValueError('Sheet recognition exceeded 15 minutes. Split the PDF into smaller sections.') from exc
            scores = sorted(output.rglob('*.mxl')) + sorted(output.rglob('*.musicxml'))
            if run.returncode or len(scores) != 1:
                detail = (run.stderr or run.stdout).decode(errors='replace')[-1500:]
                raise ValueError(f'Audiveris did not return one complete score (found {len(scores)}). Open the PDF in Audiveris to review/export it. {detail}')
            data, suffix = scores[0].read_bytes(), scores[0].suffix
        if suffix in ('.mid', '.midi'):
            midi = pretty_midi.PrettyMIDI(io.BytesIO(data))
            # MIDI carries performance timing, not an engraved score. Rebuild its
            # notation at export using the user's quantization setting.
            score = None
        else:
            xml = _xml_payload(data, suffix)
            score = converter.parseData(xml.decode('utf-8-sig'), format='musicxml')
            if starting_tempo is not None:
                if not 20 <= starting_tempo <= 300:
                    raise ValueError('Starting tempo must be between 20 and 300 BPM.')
                for mark in list(score.recurse().getElementsByClass(tempo.MetronomeMark)):
                    if mark.getOffsetInHierarchy(score) == 0:
                        mark.activeSite.remove(mark)
                (score.parts[0] if score.parts else score).insert(0, tempo.MetronomeMark(number=starting_tempo))
            midi_path = root/'performance.mid'
            playback_score = copy.deepcopy(score)
            if play_once:
                for measure in playback_score.recurse().getElementsByClass('Measure'):
                    if isinstance(measure.leftBarline, bar.Repeat):
                        measure.leftBarline = bar.Barline('regular')
                    if isinstance(measure.rightBarline, bar.Repeat):
                        measure.rightBarline = bar.Barline('regular')
                for element in list(playback_score.recurse()):
                    if isinstance(element, (repeat.RepeatExpression, spanner.RepeatBracket)):
                        element.activeSite.remove(element)
            try:
                playback_score.write('midi', fp=str(midi_path))
            except repeat.ExpanderException as exc:
                raise ValueError('Repeat markings are incomplete. Enable Play written measures once, or correct the score in Audiveris.') from exc
            midi = pretty_midi.PrettyMIDI(str(midi_path))
        if not any(inst.notes for inst in midi.instruments):
            raise ValueError('No playable notes were found in this score.')
        if midi.get_end_time() > 1200:
            raise ValueError('Score playback exceeds 20 minutes. Split the score into sections.')
        return midi, score, recognized


def score_review_warnings(score):
    if score is None:
        return []
    warnings = []
    if not any(mark.number is not None for mark in score.recurse().getElementsByClass(tempo.MetronomeMark)):
        warnings.append('No numeric tempo was recognized. Playback defaults to 120 BPM. If your score specifies a tempo, enter Starting tempo and import again.')
    overfull = []
    for part in score.parts:
        for measure in part.getElementsByClass('Measure'):
            try:
                expected = float(measure.barDuration.quarterLength)
            except Exception:
                continue
            actual = float(measure.highestTime)
            if actual > expected + .01:
                overfull.append(f'{part.partName or "Part"}, measure {measure.number}: {actual:g} quarter-note beats, expected {expected:g}')
    if overfull:
        warnings.append('Review overfull measures; these may shift later notes: ' + '; '.join(overfull[:8]) + (f' (and {len(overfull)-8} more)' if len(overfull)>8 else ''))
    return warnings
