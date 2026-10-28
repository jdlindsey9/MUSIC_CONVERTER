"""Run against local Streamlit server. Requires Playwright and Chromium."""
import os
from pathlib import Path
import pretty_midi
from playwright.sync_api import sync_playwright, expect
from music_converter.pipeline import preview_wav
m = pretty_midi.PrettyMIDI()
i = pretty_midi.Instrument(0)
for j, p in enumerate([60, 64, 67, 72]):
    i.notes.append(pretty_midi.Note(100, p, .5+j, 1.25+j))
m.instruments.append(i)
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH', '/usr/bin/chromium'), headless=True, args=['--no-sandbox'])
    page = browser.new_page()
    page.goto('http://127.0.0.1:8501')
    page.locator('input[type=file]').set_input_files(dict(name='test.wav', mimeType='audio/wav', buffer=preview_wav(m)))
    page.get_by_role('button', name='Transcribe recording').click()
    expect(page.get_by_role('button', name='Download .mxl', exact=True)).to_be_visible(timeout=180000)
    with page.expect_download() as download:
        page.get_by_role('button', name='Download .mxl', exact=True).click()
    assert Path(download.value.path()).read_bytes()[:2] == b'PK'
    page.screenshot(path='/tmp/music-converter-browser.png', full_page=True)
    page.locator('input[type=file]').set_input_files(dict(name='bad.wav', mimeType='audio/wav', buffer=b'broken'))
    expect(page.get_by_role('button', name='Download .mxl', exact=True)).to_have_count(0)
    page.get_by_role('button', name='Transcribe recording').click()
    expect(page.get_by_text('Conversion failed: Audio could not be decoded.', exact=False)).to_be_visible()
    browser.close()
print('Browser upload, real inference, MXL download, stale result clearing and corrupt upload: passed')
