from tests.test_workflow import client, report, approve


def test_original_text_preserves_whitespace(client):
    raw='  Barınak A: su gerekiyor.\n\tKaynak satırı.  \n'
    r=report(client,text=raw)
    assert r['text']==raw
    e=approve(client,r)
    assert client.get(f"/events/{e['id']}").json()['reports'][0]['text']==raw
    assert client.post('/reports',json=dict(text=' \n\t ',language='tr',source='test',location='A',need='water')).status_code==422


def test_stale_link_rejected_without_audit_or_state_change(client):
    e=approve(client,report(client));incoming=report(client);other=report(client)
    client.post(f"/reports/{other['id']}/link",json=dict(event_id=e['id'],reason='Another reviewer linked evidence'))
    payload=dict(event_id=e['id'],reason='Reviewed earlier version',expected_review_version=1,expected_event_version=1)
    assert client.post(f"/reports/{incoming['id']}/link",json=payload).status_code==409
    detail=client.get(f"/events/{e['id']}").json()
    assert len(detail['reports'])==2 and len(detail['history'])==2 and detail['version']==2
    assert client.get(f"/reports/{incoming['id']}").json()['event_id'] is None
    payload['expected_event_version']=2
    assert client.post(f"/reports/{incoming['id']}/link",json=payload).status_code==200


def test_stale_split_rejected_then_current_snapshot_succeeds(client):
    r=report(client);e=approve(client,r)
    client.patch(f"/events/{e['id']}/status",json=dict(status='in_progress',reason='Dispatch confirmed',evidence_report_id=r['id'],expected_version=1))
    payload=dict(reason='Separate verified need',expected_review_version=1,expected_event_version=1)
    assert client.post(f"/reports/{r['id']}/split",json=payload).status_code==409
    assert len(client.get('/events').json())==1
    payload.update(expected_event_version=2,expected_review_version=9)
    assert client.post(f"/reports/{r['id']}/split",json=payload).status_code==409
    payload['expected_review_version']=1
    assert client.post(f"/reports/{r['id']}/split",json=payload).status_code==201
    old=client.get(f"/events/{e['id']}").json()
    assert old['review_required']==1 and old['status']=='in_progress'
