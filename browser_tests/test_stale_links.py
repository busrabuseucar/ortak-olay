"""Second-reviewer changes must not be silently approved from a stale screen."""
import os
import httpx
from playwright.sync_api import sync_playwright, expect
from browser_tests.test_coordinator import server


def test_stale_link_and_split_screen(server):
    base, token = server
    with httpx.Client(base_url=base, headers={'Authorization':'Bearer '+token}) as api:
        def report(text):
            response=api.post('/reports',json=dict(text=text,language='tr',source='synthetic regression',location='Camp A',need='water'))
            assert response.status_code==201
            return response.json()
        source=report('First source')
        event=api.post(f"/reports/{source['id']}/new-event",json={'reason':'Confirmed initial source'}).json()
        incoming=report('  Original text with spacing.  \n')
        with sync_playwright() as p:
            options={'executable_path':os.environ['CHROMIUM_BINARY']} if os.getenv('CHROMIUM_BINARY') else {}
            browser=p.chromium.launch(headless=True,args=['--no-sandbox'],**options)
            page=browser.new_page(viewport={'width':1280,'height':900})
            page.goto(base);page.locator('#token').fill(token);page.get_by_role('button',name='Oturumu aç').click()
            page.locator(f'[data-select="{incoming["id"]}"]').click()
            expect(page.locator('#decision-form')).to_be_visible()
            assert page.locator('#detail > .source').text_content()==incoming['text']
            page.locator('#target-event').select_option(event['id'])
            def change(status,version):
                response=api.patch(f"/events/{event['id']}/status",json=dict(status=status,evidence_report_id=source['id'],expected_version=version,reason='Second reviewer update'))
                assert response.status_code==200
            change('in_progress',1)
            page.locator('#decision-reason').fill('Stale source comparison')
            page.get_by_role('button',name='Kararı onayla ve kaydet').click()
            expect(page.locator('#notice')).to_contain_text('başka bir işlemle güncellendi')
            assert api.get(f"/reports/{incoming['id']}").json()['event_id'] is None
            page.locator('#refresh').click()
            expect(page.locator('#target-event option[data-version="2"]')).to_have_count(1)
            page.locator('#target-event').select_option(event['id']);page.locator('#decision-reason').fill('Reviewed updated sources')
            page.get_by_role('button',name='Kararı onayla ve kaydet').click()
            expect(page.locator('#status-form')).to_be_visible()
            page.get_by_role('button',name='Raporu incele / bağlantıyı düzelt').last.click()
            expect(page.locator('#split-form')).to_be_visible()
            change('fulfilled',3)
            page.locator('#split-reason').fill('Stale split decision')
            page.get_by_role('button',name='Raporu ayrı kayda taşı').click()
            expect(page.locator('#notice')).to_contain_text('başka bir işlemle güncellendi')
            assert api.get(f"/reports/{incoming['id']}").json()['event_id']==event['id']
            assert len(api.get('/events').json())==1
            browser.close()
