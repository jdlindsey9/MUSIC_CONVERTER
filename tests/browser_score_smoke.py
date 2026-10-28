"""Optional real Audiveris PDF browser test; fixtures stay outside Git."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
    page=browser.new_page()
    page.goto(os.environ.get('APP_URL','http://127.0.0.1:8501'))
    page.get_by_text('Sheet music / MIDI',exact=True).click()
    page.get_by_role('textbox',name='Audiveris executable path').fill(os.environ['AUDIVERIS_PATH'])
    page.locator('input[type=file]').first.set_input_files(os.environ['SCORE_PDF'])
    page.get_by_role('button',name='Import score',exact=True).click()
    expect(page.get_by_role('button',name='Download .mid',exact=True)).to_be_visible(timeout=180000)
    with page.expect_download() as d:
        page.get_by_role('button',name='Download .mid',exact=True).click()
    assert Path(d.value.path()).read_bytes()[:4]==b'MThd'
    with page.expect_download() as d:
        page.get_by_role('button',name='Download .mxl',exact=True).click()
    assert Path(d.value.path()).read_bytes()[:2]==b'PK'
    browser.close()
print('Real PDF upload, Audiveris recognition, MIDI and MXL downloads passed.')
