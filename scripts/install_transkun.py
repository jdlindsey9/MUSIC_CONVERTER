"""Build a metadata-only Windows-compatible wheel from official Transkun 2.0.1.

The declared ncls dependency has no Windows wheel and is used by dataset indexing, not the inference path. Move it to an
optional training extra. Preserve code, checkpoint and licenses byte-for-byte. Abort if
that assumption changes. Keep the local version explicit for provenance.
"""
import csv
import ast
import hashlib
import io
import base64
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

VERSION = '2.0.1+musicconverter.1'


def patch_wheel(source, destination):
    with zipfile.ZipFile(source) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    for name, data in entries.items():
        if not name.endswith('.py'):
            continue
        tree = ast.parse(data)
        allowed = set()
        if name == 'transkun/Data.py':
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.name == 'createIndexEvents':
                    allowed.update(id(child) for child in ast.walk(node))
        for node in ast.walk(tree):
            imports_ncls = (isinstance(node, ast.ImportFrom) and node.module == 'ncls') or (isinstance(node, ast.Import) and any(a.name == 'ncls' for a in node.names))
            if imports_ncls and id(node) not in allowed:
                raise RuntimeError('Unexpected ncls import outside dataset indexing; refusing to patch.')
    metadata_name = next(n for n in entries if n.endswith('.dist-info/METADATA'))
    metadata = entries[metadata_name].decode()
    if 'Version: 2.0.1\n' not in metadata or 'Requires-Dist: ncls\n' not in metadata:
        raise RuntimeError('Unexpected Transkun metadata; refusing to change this wheel.')
    metadata = metadata.replace('Version: 2.0.1\n', f'Version: {VERSION}\n').replace('Requires-Dist: ncls\n', 'Provides-Extra: training\nRequires-Dist: ncls; extra == "training"\n')
    entries[metadata_name] = metadata.encode()
    old = metadata_name.split('/')[0]
    new = f'transkun-{VERSION}.dist-info'
    entries = {name.replace(old+'/',new+'/',1):data for name,data in entries.items() if not name.endswith('.dist-info/RECORD')}
    record = io.StringIO(newline='')
    writer = csv.writer(record,lineterminator='\n')
    for name,data in entries.items():
        digest=base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode()
        writer.writerow([name,'sha256='+digest,len(data)])
    writer.writerow([new+'/RECORD','',''])
    entries[new+'/RECORD']=record.getvalue().encode()
    path = Path(destination)/f'transkun-{VERSION}-py3-none-any.whl'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in entries.items():
            archive.writestr(name,data)
    return path


if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as work:
        subprocess.run([sys.executable,'-m','pip','download','--no-deps','--only-binary=:all:','transkun==2.0.1','-d',work],check=True)
        source=next(Path(work).glob('transkun-2.0.1-*.whl'))
        wheel=patch_wheel(source,work)
        subprocess.run([sys.executable,'-m','pip','install',str(wheel)],check=True)
