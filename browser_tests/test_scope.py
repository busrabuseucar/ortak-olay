"""Reviewer-entered scope is visible, correctable before linking and enforced by API."""
import os
from playwright.sync_api import sync_playwright, expect
from browser_tests.test_coordinator import server


def test_report_scope_journey(server):
    base, token = server
    with sync_playwright() as p:
        options = {'executable_path': os.environ['CHROMIUM_BINARY']} if os.getenv('CHROMIUM_BINARY') else {}
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'], **options)
        page = browser.new_page(viewport={'width': 1280, 'height': 900})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(base)
        page.locator('#token').fill(token)
        page.get_by_role('button', name='Oturumu aç').click()
        expect(page.locator('#dashboard')).to_be_visible()

        def add(text, group, kind):
            page.locator('#add-report').click()
            page.locator('#report-text').fill(text)
            page.locator('#report-source').fill('Synthetic scope exercise')
            page.locator('#report-location').fill('Camp A')
            page.locator('#report-group').fill(group)
            page.locator('#report-statement').select_option(kind)
            page.get_by_role('button', name='Raporu kaydet', exact=True).click()
            expect(page.locator('#report-dialog')).not_to_be_visible()
            expect(page.locator('#detail > .source')).to_have_text(text)

        def new_event():
            page.locator('#target-event').select_option('')
            page.locator('#decision-reason').fill('Kaynak ve grup doğrulandı')
            page.get_by_role('button', name='Kararı onayla ve kaydet').click()
            expect(page.locator('#status-form')).to_be_visible()

        add('Tent 12 needs water.', 'tent-12', 'need')
        new_event()
        first_id = page.locator('.record[aria-current=true]').get_attribute('data-select')
        expect(page.locator('#detail')).to_contain_text('Grup: tent-12')
        add('Tent 98 needs water.', 'tent-98', 'need')
        expect(page.locator('.candidate')).to_have_count(0)
        expect(page.locator('#detail')).to_contain_text('Grup kodu farklı')
        page.locator('#target-event').select_option(first_id)
        page.locator('#decision-reason').fill('Yanlış grup bağlantısı denemesi')
        page.get_by_role('button', name='Kararı onayla ve kaydet').click()
        expect(page.locator('#notice')).to_contain_text('Grup kodları farklı')
        expect(page.locator('#active-count')).to_have_text('1')
        new_event()
        expect(page.locator('#active-count')).to_have_text('2')
        # Wrong human classification can be corrected without replacing the source text.
        original = 'Tent 12 reports that water is still needed.'
        add(original, 'tent-12', 'hypothetical')
        expect(page.locator('#decision-form')).to_have_count(0)
        expect(page.locator('#detail')).to_contain_text('İhtiyaç önerileri ve ihtiyaç oluşturma kapalı')
        page.locator('#review-statement').select_option('need')
        page.locator('#review-reason').fill('Kaynakla görüşüldü; gerçek ihtiyaç bildirimi')
        page.get_by_role('button', name='Değerlendirmeyi kaydet').click()
        expect(page.locator('#decision-form')).to_be_visible()
        expect(page.locator('#detail > .source')).to_have_text(original)
        expect(page.locator('#detail')).to_contain_text('Değerlendirme geçmişi')
        expect(page.locator('.candidate')).to_have_count(1)
        page.locator('#target-event').select_option(first_id)
        page.locator('#decision-reason').fill('Aynı çadırın güncel ihtiyacı doğrulandı')
        page.get_by_role('button', name='Kararı onayla ve kaydet').click()
        expect(page.locator('#detail .detail-header .badge')).to_have_text('Açık')
        page.get_by_role('button', name='Raporu incele / bağlantıyı düzelt').last.click()
        expect(page.locator('#review-form')).to_have_count(0)
        expect(page.locator('#detail')).to_contain_text('Kaynakla görüşüldü; gerçek ihtiyaç bildirimi')
        page.set_viewport_size({'width': 390, 'height': 844})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert not errors, errors
        browser.close()
