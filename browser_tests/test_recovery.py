import os
from playwright.sync_api import sync_playwright, expect
from browser_tests.test_coordinator import server


def test_rejection_restore_and_linked_correction(server):
    base, token = server
    with sync_playwright() as p:
        options = {'executable_path': os.environ['CHROMIUM_BINARY']} if os.getenv('CHROMIUM_BINARY') else {}
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'], **options)
        page = browser.new_page(viewport={'width':1280,'height':900})
        errors=[]; page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(base); page.locator('#token').fill(token)
        page.get_by_role('button', name='Oturumu aç').click()
        expect(page.locator('#dashboard')).to_be_visible()
        def add(text):
            page.locator('#add-report').click()
            page.locator('#report-text').fill(text)
            page.locator('#report-source').fill('Synthetic recovery exercise')
            page.locator('#report-location').fill('Camp A')
            page.locator('#report-group').fill('tent-12')
            page.locator('#report-statement').select_option('need')
            page.get_by_role('button', name='Raporu kaydet', exact=True).click()
            expect(page.locator('#detail > .source')).to_have_text(text)
        add('First water request')
        page.locator('#decision-reason').fill('Source checked')
        page.get_by_role('button', name='Kararı onayla ve kaydet').click()
        expect(page.locator('#status-form')).to_be_visible()
        add('Second water request')
        expect(page.locator('.candidate')).to_have_count(1)
        page.locator('.candidate-decision textarea').fill('Different household confirmed')
        page.get_by_role('button', name='Öneriyi reddet', exact=True).click()
        expect(page.locator('.candidate')).to_have_count(0)
        page.locator('#refresh').click()
        expect(page.get_by_role('button', name='Yeniden değerlendirmeye aç')).to_be_visible()
        page.locator('.candidate-decision textarea').fill('New coordinator verification')
        page.get_by_role('button', name='Yeniden değerlendirmeye aç', exact=True).click()
        expect(page.locator('.candidate')).to_have_count(1)
        page.get_by_role('button', name='Karar için bu kaydı seç').click()
        page.locator('#decision-reason').fill('Same household after clarification')
        page.get_by_role('button', name='Kararı onayla ve kaydet').click()
        expect(page.locator('#status-form')).to_be_visible()
        page.get_by_role('button', name='Raporu incele / bağlantıyı düzelt').last.click()
        page.locator('#review-group').fill('tent-98')
        page.locator('#review-detach').check()
        page.locator('#review-reason').fill('Corrected group after source confirmation')
        page.get_by_role('button', name='Değerlendirmeyi kaydet', exact=True).click()
        expect(page.locator('#decision-form')).to_be_visible()
        expect(page.locator('#detail > .source')).to_have_text('Second water request')
        page.locator('#events-tab').click()
        expect(page.locator('#record-list')).to_contain_text('Yeniden inceleme gerekli')
        page.locator('#record-list button').first.click()
        expect(page.locator('#detail')).to_contain_text('Önceki durum korunuyor')
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.screenshot(path='/tmp/ortak-recovery.png', full_page=True)
        assert not errors
        browser.close()
