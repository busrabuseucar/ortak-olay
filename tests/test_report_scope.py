import json
import sqlite3
import pytest
from fastapi.testclient import TestClient
from app.main import create_app, SCHEMA
from tests.test_workflow import TOKEN, report, approve, client
from tests.test_matching import Encoder


def review(c, r, **changes):
    data = dict(group_ref=r['group_ref'], statement_type=r['statement_type'], expected_review_version=r['review_version'], reason='Source checked by coordinator')
    return c.patch(f"/reports/{r['id']}/review", json=data | changes)


@pytest.mark.parametrize('kind', ['hypothetical', 'general_info'])
def test_non_factual_cannot_open_link_or_suggest(client, kind):
    e = approve(client, report(client))
    r = report(client, statement_type=kind)
    result = client.get(f"/reports/{r['id']}/suggestions").json()
    assert result['candidates'] == []
    assert result['matching']['blocked_reason'] == 'non_factual_report'
    assert client.post(f"/reports/{r['id']}/new-event", json={'reason': 'Attempt to approve'}).status_code == 422
    assert client.post(f"/reports/{r['id']}/link", json={'event_id': e['id'], 'reason': 'Attempt to link'}).status_code == 422
    assert len(client.get('/events').json()) == 1


def test_group_conflict_rejected_and_separate_event_keeps_scope(client):
    e = approve(client, report(client, group_ref='tent-12', statement_type='need'))
    r = report(client, group_ref='tent-98', statement_type='need')
    result = client.get(f"/reports/{r['id']}/suggestions").json()
    assert result['candidates'] == []
    assert result['matching']['excluded_groups'][0]['group_ref'] == 'tent-12'
    assert client.post(f"/reports/{r['id']}/link", json={'event_id':e['id'], 'reason':'Wrong group'}).status_code == 422
    other = approve(client, r)
    assert other['group_ref'] == 'tent-98'
    assert client.get(f"/events/{e['id']}").json()['group_ref'] == 'tent-12'


def test_unknown_scope_is_warned_and_delivery_does_not_close(client):
    e = approve(client, report(client, group_ref='TENT-12', statement_type='need'))
    r = report(client)
    c = client.get(f"/reports/{r['id']}/suggestions").json()['candidates'][0]
    assert {'group_unknown', 'statement_type_unknown'} <= set(c['flags'])
    delivery = report(client, text='Water delivered', statement_type='update', group_ref='tent-12')
    assert client.post(f"/reports/{delivery['id']}/link", json={'event_id':e['id'], 'reason':'Same group confirmed'}).status_code == 200
    assert client.get(f"/events/{e['id']}").json()['status'] == 'open'


def test_review_is_audited_and_cannot_overwrite_stale_decision(client):
    r = report(client, statement_type='hypothetical')
    response = review(client, r, statement_type='need', group_ref='tent-12')
    assert response.status_code == 200
    updated = response.json()
    assert updated['text'] == r['text']
    assert updated['review_version'] == 2
    assert review(client, r, statement_type='general_info').status_code == 409
    detail = client.get(f"/reports/{r['id']}").json()
    h = detail['review_history'][0]
    assert h['actor'] == 'test-reviewer'
    assert json.loads(h['details'])['before']['statement_type'] == 'hypothetical'
    assert json.loads(h['details'])['after']['group_ref'] == 'tent-12'
    assert client.post(f"/reports/{r['id']}/new-event", json={'reason':'Stale screen', 'expected_review_version':1}).status_code == 409
    approve(client, updated)
    assert review(client, updated, group_ref='tent-98').status_code == 409


def test_invalid_review_preserves_source(client):
    r = report(client)
    for changes in [{'group_ref':' '}, {'statement_type':'confirmed_by_AI'}, {'text':'rewrite source'}, {'reason':' '}]:
        assert review(client, r, **changes).status_code == 422
    assert client.get(f"/reports/{r['id']}").json()['text'] == r['text']
    client.headers.pop('Authorization')
    assert client.get(f"/reports/{r['id']}").status_code == 401
    assert review(client, r).status_code == 401


def test_migration_preserves_existing_linked_data_and_is_repeatable(tmp_path):
    path = str(tmp_path / 'legacy.db')
    with sqlite3.connect(path) as db:
        db.executescript(SCHEMA)
        db.execute("INSERT INTO events VALUES('e','Site','water','fulfilled',3,'2026-09-01T10:00:00Z')")
        db.execute("INSERT INTO reports VALUES('r','Original text','en','source','Site','water',20,'people',NULL,'2026-09-01T10:00:00Z','e')")
        db.execute("INSERT INTO audit(timestamp,actor,action,event_id,details) VALUES('2026-09-01','reviewer','status_changed','e','{}')")
    for _ in range(2):
        with TestClient(create_app(path, {TOKEN:'reviewer'})) as c:
            c.headers['Authorization'] = 'Bearer '+TOKEN
            e = c.get('/events/e').json()
            r = c.get('/reports/r').json()
            assert (e['status'], e['version'], len(e['history'])) == ('fulfilled', 3, 1)
            assert r['text'] == 'Original text' and r['event_id'] == 'e'
            assert r['group_ref'] is None and r['statement_type'] == 'unknown' and r['review_version'] == 1


def test_semantic_score_does_not_override_scope(tmp_path):
    with TestClient(create_app(str(tmp_path/'semantic.db'), {TOKEN:'reviewer'}, Encoder([.999]))) as c:
        c.headers['Authorization'] = 'Bearer '+TOKEN
        approve(c, report(c, group_ref='tent-12'))
        r = report(c, group_ref='tent-98')
        result = c.get(f"/reports/{r['id']}/suggestions").json()
        assert not result['candidates'] and result['matching']['excluded_groups']
        r = report(c, statement_type='hypothetical')
        result = c.get(f"/reports/{r['id']}/suggestions").json()
        assert result['matching']['blocked_reason'] == 'non_factual_report'


def test_unscoped_founder_does_not_hide_later_known_group_conflict(client):
    e = approve(client, report(client))
    first = report(client, group_ref='tent-12')
    assert client.post(f"/reports/{first['id']}/link", json={'event_id':e['id'], 'reason':'Group confirmed'}).status_code == 200
    other = report(client, group_ref='tent-98')
    result = client.get(f"/reports/{other['id']}/suggestions").json()
    assert not result['candidates']
    assert result['matching']['excluded_groups'][0]['group_ref'] == 'tent-12'
    assert client.post(f"/reports/{other['id']}/link", json={'event_id':e['id'], 'reason':'Wrong group'}).status_code == 422
