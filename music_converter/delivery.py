"""Durable local results and browser media independent of /media URLs."""
import base64
import html
import io
import json
import zipfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4


def audio_html(data, mime='audio/wav'):
    # Embed source bytes so playback doesn't depend on Streamlit's media server.
    payload = base64.b64encode(data).decode('ascii')
    return f'<audio controls preload="metadata" style="width:100%" src="data:{html.escape(mime, quote=True)};base64,{payload}"></audio>'


def download_html(data, filename):
    payload = base64.b64encode(data).decode('ascii')
    return f'<a download="{html.escape(filename, quote=True)}" href="data:application/octet-stream;base64,{payload}" style="color:#7cc4ff">Save MIDI directly</a>'


def save_results(files, original, preview, metadata, stem=None, root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parents[1] / 'outputs'
    path = root / (datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid4().hex[:8])
    path.mkdir(parents=True, exist_ok=False)
    payload = {f'transcription.{ext}': data for ext, data in files.items()}
    payload.update({'original-detected.mid': original, 'preview.wav': preview,
                    'result.json': json.dumps(metadata, indent=2).encode()})
    if stem is not None:
        payload['isolated-piano.wav'] = stem
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in payload.items():
            (path / name).write_bytes(data)
            z.writestr(name, data)
    (path / 'all-files.zip').write_bytes(archive.getvalue())
    return str(path), archive.getvalue()
