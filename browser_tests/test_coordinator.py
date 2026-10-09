"""Real browser regression: all mutations use the coordinator interface."""
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

import pytest
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def server(tmp_path):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    token = secrets.token_urlsafe(32)
    env = os.environ | {'ORTAK_DB': str(tmp_path / 'browser.db'), 'ORTAK_REVIEWERS': json.dumps({token: 'Browser reviewer'})}
    process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:create_app', '--factory', '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    base = f'http://127.0.0.1:{port}'
    try:
        for _ in range(100):
            if process.poll() is not None:
                raise RuntimeError(process.stderr.read().decode())
            try:
                with urlopen(base + '/health', timeout=1):
                    break
            except OSError:
                time.sleep(.1)
        else:
            raise RuntimeError('Local server did not start')
        yield base, token
    finally:
        process.terminate()
        process.wait(timeout=10)


def test_coordinator_journey(server):
    base, token = server
    with sync_playwright() as p:
        options = {'executable_path': os.environ['CHROMIUM_BINARY']} if os.getenv('CHROMIUM_BINARY') else {}
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'], **options)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(base)
        page.locator('#token').fill('invalid')
        page.get_by_role('button', name='Oturumu aç').click()
        expect(page.locator('#notice')).to_contain_text('geçersiz')
        page.locator('#token').fill(token)
        page.get_by_role('button', name='Oturumu aç').click()
        expect(page.locator('#dashboard')).to_be_visible()
        expect(page.locator('#pending-count')).to_have_text('0')

        def add(text, need='water', quantity='', unit='', language='tr', location='Barınak A'):
            page.get_by_role('button', name='+ Yeni rapor').click()
            page.locator('#report-text').fill(text)
            page.locator('#report-source').fill('Synthetic browser exercise')
            page.locator('#report-location').fill(location)
            page.locator('#report-language').select_option(language)
            page.locator('#report-need').select_option(need)
            page.locator('#report-quantity').fill(quantity)
            page.locator('#report-unit').fill(unit)
            page.locator('#report-time').fill('2026-09-01T10:00')
            page.get_by_role('button', name='Raporu kaydet', exact=True).click()
            expect(page.locator('#report-dialog')).not_to_be_visible()
            expect(page.locator('#decision-form')).to_be_visible()
            expect(page.locator('#detail > .source')).to_have_text(text)

        def decide(reason, target=None):
            if target:
                page.locator('#target-event').select_option(target)
            page.locator('#decision-reason').fill(reason)
            page.get_by_role('button', name='Kararı onayla ve kaydet').click()
            expect(page.locator('#status-form')).to_be_visible()

        add('Barınak A: 20 kişinin suya ihtiyacı var.', quantity='20', unit='kişi')
        decide('Konum ve ihtiyaç doğrulandı')
        water_id = page.locator('.record[aria-current=true]').get_attribute('data-select')
        add('Shelter A: 30 people need water.', quantity='30', unit='kişi', language='en')
        expect(page.locator('.flags')).to_contain_text('Miktarlar çelişiyor')
        if os.getenv('ORTAK_MATCHER') == 'semantic':
            expect(page.locator('#detail')).to_contain_text('Yerel çok dilli model')
            expect(page.locator('.candidate')).to_contain_text('Benzerlik:')
        else:
            expect(page.locator('#detail')).to_contain_text('Anlamsal model etkin değil')
        screenshots = os.getenv('ORTAK_SCREENSHOTS')
        if screenshots:
            Path(screenshots).mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(Path(screenshots) / 'coordinator-desktop.png'), full_page=True)
        page.get_by_role('button', name='Karar için bu kaydı seç').click()
        decide('Aynı grup olduğu kontrol edildi', water_id)
        add('Water delivered; diapers still needed.', language='en')
        decide('Teslimat raporu aynı konuma ait', water_id)
        page.locator('#event-status').select_option('fulfilled')
        page.locator('#evidence-report').select_option(index=3)
        page.locator('#status-reason').fill('Su teslimatı doğrulandı')
        page.get_by_role('button', name='Durumu kaydet', exact=True).click()
        expect(page.locator('#detail .detail-header .badge')).to_have_text('Karşılandı')
        add('Water delivered; diapers still needed.', need='diapers', language='en')
        decide('Bebek bezi ihtiyacı ayrı ve açık')
        expect(page.locator('#active-count')).to_have_text('1')
        expect(page.locator('#closed-count')).to_have_text('1')
        add('Barınak A: 20 kişinin suya ihtiyacı var.', quantity='20', unit='kişi')
        expect(page.locator('.flags')).to_contain_text('Eski mesajın tekrarı olabilir')
        expect(page.locator('.flags')).to_contain_text('Karşılanmış ihtiyaç')
        expect(page.locator('#closed-count')).to_have_text('1')
        expect(page.locator('#pending-count')).to_have_text('1')

        # Split preserves historical status but puts the source event back into review.
        decide('Tatbikat için tekrar kaydı bağlandı', water_id)
        page.get_by_role('button', name='Raporu incele / bağlantıyı düzelt').last.click()
        page.locator('#split-reason').fill('Farklı grup olduğu doğrulandı')
        page.get_by_role('button', name='Raporu ayrı kayda taşı').click()
        expect(page.locator('#detail')).to_contain_text('Rapor ayrı bir kayda taşındı')
        expect(page.locator('#active-count')).to_have_text('3')
        expect(page.locator('#closed-count')).to_have_text('0')
        expect(page.locator('#record-list')).to_contain_text('Karşılandı · Yeniden inceleme gerekli')

        # Stale reviewer decisions must remain visible and must not overwrite newer data.
        page.locator('#status-reason').fill('Eski ekran üzerinden karar')
        page.locator('#evidence-report').select_option(index=1)
        page.locator('#event-status').select_option('fulfilled')
        current_id = page.locator('.record[aria-current=true]').get_attribute('data-select')
        current = page.request.get(base + '/events/' + current_id, headers={'Authorization': 'Bearer ' + token}).json()
        response = page.request.patch(base + '/events/' + current_id + '/status', headers={'Authorization': 'Bearer ' + token}, data={'status': 'in_progress', 'evidence_report_id': current['reports'][0]['id'], 'expected_version': current['version'], 'reason': 'Concurrent reviewer decision'})
        assert response.status == 200
        page.get_by_role('button', name='Durumu kaydet', exact=True).click()
        expect(page.locator('#notice')).to_contain_text('başka bir işlemle güncellendi')
        expect(page.locator('#status-reason')).to_have_value('Eski ekran üzerinden karar')
        page.get_by_role('button', name='Yenile', exact=True).click()
        expect(page.locator('#detail .detail-header .badge')).to_have_text('İşlemde')

        # Source text must be rendered as text, not executable markup.
        attack = '<img src=x onerror="window.injected=true"> Kaynak mesajı'
        add(attack)
        expect(page.locator('#detail > .source')).to_have_text(attack)
        assert page.evaluate('window.injected === undefined')
        assert page.locator('#detail img').count() == 0
        page.set_viewport_size({'width': 390, 'height': 844})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        if screenshots:
            page.screenshot(path=str(Path(screenshots) / 'coordinator-mobile.png'), full_page=True)

        # Validation keeps the form open and user's input intact.
        page.get_by_role('button', name='+ Yeni rapor').click()
        page.locator('#report-text').fill('Eksik birim örneği')
        page.locator('#report-source').fill('Tatbikat')
        page.locator('#report-location').fill('Barınak A')
        page.locator('#report-quantity').fill('10')
        page.get_by_role('button', name='Raporu kaydet', exact=True).click()
        expect(page.locator('#form-error')).to_contain_text('Miktar ve birimi')
        expect(page.locator('#report-text')).to_have_value('Eksik birim örneği')
        page.get_by_role('button', name='Pencereyi kapat').click()
        if os.getenv('ORTAK_MATCHER') == 'semantic':
            add('Shelter B: 30 people need water.', language='en', location='Shelter B')
            expect(page.locator('#detail')).to_contain_text('Konum kodu farklı olduğu için önerilmedi')
            expect(page.locator('.candidate')).to_have_count(0)
            # Human correction remains possible; this is a synthetic label-error decision.
            decide('Tatbikat: kaynak konum etiketinin yanlış olduğu doğrulandı', water_id)
            expect(page.locator('#detail .detail-header .badge')).to_have_text('Karşılandı · Yeniden inceleme gerekli')
        page.get_by_role('button', name='Oturumu kapat', exact=True).click()
        expect(page.locator('#dashboard')).not_to_be_visible()
        assert page.locator('#detail').inner_text() == ''
        assert page.evaluate('localStorage.length + sessionStorage.length') == 0
        assert not errors, errors
        browser.close()
