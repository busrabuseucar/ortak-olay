import json
from fastapi.testclient import TestClient
from app.main import create_app
from tests.test_workflow import TOKEN, report, approve, client
from tests.test_report_scope import review


def candidate(c, r, e, action='reject', version=0, **overrides):
    return c.post(f"/reports/{r['id']}/candidate-decision", json=dict(event_id=e['id'], action=action, reason='Separate households checked', expected_review_version=r['review_version'], expected_event_version=e['version'], expected_decision_version=version) | overrides)


def test_linked_correction_and_status_revalidation(client):
    r = report(client, group_ref='tent-12', statement_type='need'); e = approve(client, r)
    client.patch(f"/events/{e['id']}/status", json=dict(status='fulfilled', evidence_report_id=r['id'], expected_version=1, reason='Delivery confirmed'))
    assert review(client, r, group_ref='tent-98').status_code == 409
    assert review(client, r, group_ref='tent-98', detach_linked=True, expected_event_version=1).status_code == 409
    result = review(client, r, group_ref='tent-98', detach_linked=True, expected_event_version=2)
    assert result.status_code == 200
    new = result.json()
    assert new['event_id'] is None and new['text'] == r['text'] and new['review_version'] == 2
    old = client.get(f"/events/{e['id']}").json()
    assert old['review_required'] == 1 and old['status'] == 'fulfilled' and old['version'] == 3
    assert old['reports'] == [] and len(old['history']) == 3
    payload = dict(status='fulfilled', evidence_report_id=r['id'], expected_version=3, reason='Reaffirm status')
    assert client.patch(f"/events/{e['id']}/status", json=payload).status_code == 422
    assert review(client, r, statement_type='general_info').status_code == 409
    replacement = report(client, group_ref='tent-12')
    client.post(f"/reports/{replacement['id']}/link", json=dict(event_id=e['id'],reason='Independent source checked'))
    payload.update(evidence_report_id=replacement['id'], expected_version=4)
    assert client.patch(f"/events/{e['id']}/status", json=payload).status_code == 200
    assert client.get(f"/events/{e['id']}").json()['review_required'] == 0


def test_nonfactual_correction_does_not_create_need(client):
    r = report(client, statement_type='need'); e = approve(client, r)
    assert review(client, r, statement_type='hypothetical', detach_linked=True, expected_event_version=1).status_code == 200
    assert len(client.get('/events').json()) == 1
    assert not client.get(f"/reports/{r['id']}/suggestions").json()['candidates']
    assert client.post(f"/reports/{r['id']}/new-event", json={'reason':'Wrong approval'}).status_code == 422


def test_reject_restore_and_stale_guards(client):
    e = approve(client, report(client)); r = report(client)
    assert candidate(client, r, e).status_code == 200
    s = client.get(f"/reports/{r['id']}/suggestions").json()
    assert not s['candidates'] and s['rejections'][0]['active']
    assert candidate(client, r, e).status_code == 409
    assert client.post(f"/reports/{r['id']}/link", json=dict(event_id=e['id'],reason='Bypass rejected suggestion')).status_code == 409
    assert candidate(client, r, e, 'restore', 1).status_code == 200
    assert len(client.get(f"/reports/{r['id']}/suggestions").json()['candidates']) == 1
    assert candidate(client, r, e, 'restore', 1).status_code == 409
    assert candidate(client, r, e, version=2).status_code == 200
    extra = report(client)
    client.post(f"/reports/{extra['id']}/link", json=dict(event_id=e['id'],reason='Additional source'))
    s = client.get(f"/reports/{r['id']}/suggestions").json()
    assert len(s['candidates']) == 1 and not s['rejections'][0]['active']
    assert candidate(client, r, e, 'restore', 3).status_code == 409
    history = client.get(f"/reports/{r['id']}").json()['review_history']
    assert [h['action'] for h in history] == ['candidate_reject','candidate_restore','candidate_reject']
    assert all(json.loads(h['details'])['reason'] for h in history)


def test_rejection_survives_restart_and_requires_auth(tmp_path):
    path = str(tmp_path/'review.db')
    with TestClient(create_app(path, {TOKEN:'reviewer'})) as c:
        c.headers['Authorization'] = 'Bearer '+TOKEN
        e = approve(c, report(c)); r = report(c)
        assert candidate(c, r, e).status_code == 200
    with TestClient(create_app(path, {TOKEN:'reviewer'})) as c:
        assert candidate(c, r, e).status_code == 401
        c.headers['Authorization'] = 'Bearer '+TOKEN
        assert c.get(f"/reports/{r['id']}/suggestions").json()['rejections'][0]['active']
        assert candidate(c, r, e, 'restore', 1, reason=' ').status_code == 422
