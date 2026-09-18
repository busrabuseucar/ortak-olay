"""Deterministic contract tests; real model measurements live in evaluation/."""
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.matching import suggest
from tests.test_workflow import TOKEN, report, approve


class Encoder:
    metadata = {'model': 'test-double'}

    def __init__(self, values):
        self.values = values

    def similarities(self, query, documents):
        return self.values


def records():
    r = dict(id='new', event_id=None, need='water', location='Barınak A',
             text='Su gerekiyor.', quantity=20, unit='people', reported_at='2026-09-01T10:00:00+00:00')
    source = r | dict(id='old', text='Water needed.', location='Shelter A')
    e = dict(id='event', need='water', location='Shelter A', status='open')
    return r, e, source


def test_semantic_candidate_has_evidence_and_does_not_mutate():
    r, e, source = records()
    before = deepcopy((r, e, source))
    assert suggest(r, [(e, [source])])['candidates'] == []
    result = suggest(r, [(e, [source])], Encoder([.91]))
    c = result['candidates'][0]
    assert c['method'] == 'semantic-v1'
    assert c['semantic_evidence_report_id'] == source['id']
    assert 'location_unverified' in c['flags']
    assert not result['automatic_linking']
    assert not result['matching']['score_is_probability']
    assert (r, e, source) == before


@pytest.mark.parametrize('values', [[float('nan')], [float('inf')], [1.1], []])
def test_bad_model_output_returns_labelled_baseline(values):
    r, e, source = records()
    r['location'] = e['location']
    result = suggest(r, [(e, [source])], Encoder(values))
    assert result['matching']['active'] == 'baseline'
    assert result['matching']['warning'] == 'semantic_unavailable'
    assert result['candidates'][0]['similarity'] is None


def test_model_exception_does_not_leak_or_drop_baseline():
    class Broken:
        def similarities(self, *args):
            raise RuntimeError('private report contents')
    r, e, source = records()
    r['location'] = e['location']
    result = suggest(r, [(e, [source])], Broken())
    assert 'private report' not in str(result)
    assert len(result['candidates']) == 1


def test_gates_and_baseline_retention():
    r, e, source = records()
    assert not suggest(r, [(e | {'need': 'food'}, [source])], Encoder([1]))['candidates']
    old = source | {'reported_at': '2026-08-01T10:00:00+00:00'}
    assert not suggest(r, [(e, [old])], Encoder([1]))['candidates']
    assert not suggest(r | {'event_id': e['id']}, [(e, [source])], Encoder([1]))['candidates']
    r['location'] = e['location']
    c = suggest(r, [(e, [source])], Encoder([.1]))['candidates'][0]
    assert c['method'] == 'structured-baseline-v1'
    assert c['similarity'] == .1
    c = suggest(r, [(e, [source])], Encoder([.9]))['candidates'][0]
    assert c['method'] == 'baseline+semantic-v1'


def test_best_source_and_conflicts():
    r, e, source = records()
    second = source | {'id': 'second', 'quantity': 30, 'reported_at': None}
    c = suggest(r, [(e | {'status': 'fulfilled'}, [source, second])], Encoder([.4, .9]))['candidates'][0]
    assert c['semantic_evidence_report_id'] == 'second'
    assert {'quantity_conflict', 'unknown_event_time', 'fulfilled_need_requires_review'} <= set(c['flags'])


def test_api_integration_keeps_decision_manual(tmp_path):
    with TestClient(create_app(str(tmp_path / 'ai.db'), {TOKEN: 'reviewer'}, Encoder([.92]))) as c:
        c.headers['Authorization'] = f'Bearer {TOKEN}'
        event = approve(c, report(c))
        r = report(c, location='Barınak A', language='tr', text='Barınak A için su gerekiyor.')
        before = c.get(f"/events/{event['id']}").json()
        result = c.get(f"/reports/{r['id']}/suggestions").json()
        assert result['matching']['active'] == 'semantic'
        assert result['candidates'][0]['event_id'] == event['id']
        assert c.get(f"/events/{event['id']}").json() == before
        assert c.get('/reports?pending=true').json()[0]['id'] == r['id']
