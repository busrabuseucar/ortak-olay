from fastapi.testclient import TestClient
import pytest

from app.main import create_app

TOKEN = "test-only-token-not-for-deployment-123"


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(str(tmp_path / "test.db"), {TOKEN: "test-reviewer"})) as c:
        c.headers["Authorization"] = f"Bearer {TOKEN}"
        yield c


def report(client, **changes):
    data = dict(text="Shelter A: 20 people need water.", language="en", source="synthetic-exercise",
                location="Shelter A", need="water", quantity=20, unit="people",
                reported_at="2026-09-01T10:00:00Z")
    data.update(changes)
    response = client.post("/reports", json=data)
    assert response.status_code == 201, response.text
    return response.json()


def approve(client, r):
    response = client.post(f"/reports/{r['id']}/new-event", json={"reason": "Checked exercise report"})
    assert response.status_code == 201
    return response.json()


def test_application_scenario(client):
    first = report(client, text="Barınak A: 20 kişinin suya ihtiyacı var.", language="tr")
    water = approve(client, first)
    second = report(client, text="Shelter A: 30 people need water.", quantity=30)
    suggestion = client.get(f"/reports/{second['id']}/suggestions").json()
    assert suggestion["automatic_linking"] is False
    assert "quantity_conflict" in suggestion["candidates"][0]["flags"]
    assert client.get("/reports?pending=true").json()[0]["id"] == second["id"]
    assert client.post(f"/reports/{second['id']}/link", json={"event_id": water["id"], "reason": "Confirmed same group"}).status_code == 200
    delivery = report(client, text="Water delivered; diapers still needed.", quantity=None, unit=None)
    client.post(f"/reports/{delivery['id']}/link", json={"event_id": water["id"], "reason": "Delivery evidence"})
    diapers = approve(client, report(client, text=delivery["text"], need="diapers", quantity=None, unit=None))
    current = client.get(f"/events/{water['id']}").json()
    result = client.patch(f"/events/{water['id']}/status", json={"status": "fulfilled", "evidence_report_id": delivery["id"], "expected_version": current["version"], "reason": "Delivery scope confirmed"})
    assert result.status_code == 200
    assert client.get(f"/events/{diapers['id']}").json()["status"] == "open"
    repost = report(client, text=first["text"], language="tr")
    flags = client.get(f"/reports/{repost['id']}/suggestions").json()["candidates"][0]["flags"]
    assert "possible_repost" in flags
    assert "fulfilled_need_requires_review" in flags
    assert client.get(f"/events/{water['id']}").json()["status"] == "fulfilled"
    history = client.get(f"/events/{water['id']}").json()["history"]
    assert history[-1]["actor"] == "test-reviewer"
    assert history[-1]["action"] == "status_changed"


def test_authentication(client):
    client.headers.pop("Authorization")
    assert client.get("/reports").status_code == 401
    assert client.get("/events").status_code == 401
    assert client.post("/reports", json={}).status_code == 401
    client.headers["Authorization"] = "Bearer invalid"
    assert client.get("/events").status_code == 401


def test_cannot_silently_overwrite_decision(client):
    r = report(client)
    e = approve(client, r)
    action = dict(status="fulfilled", evidence_report_id=r["id"], expected_version=1, reason="Checked evidence")
    assert client.patch(f"/events/{e['id']}/status", json=action).status_code == 200
    action["status"] = "open"
    assert client.patch(f"/events/{e['id']}/status", json=action).status_code == 409
    assert client.get(f"/events/{e['id']}").json()["status"] == "fulfilled"


def test_status_requires_linked_evidence(client):
    a, b = report(client), report(client)
    e = approve(client, a)
    assert client.patch(f"/events/{e['id']}/status", json=dict(status="fulfilled", evidence_report_id=b["id"], expected_version=1, reason="Unlinked evidence")).status_code == 422


def test_split_preserves_source_and_history(client):
    a, b = report(client), report(client, quantity=30)
    e = approve(client, a)
    client.post(f"/reports/{b['id']}/link", json={"event_id": e["id"], "reason": "Initial grouping"})
    separated = client.post(f"/reports/{b['id']}/split", json={"reason": "Different group confirmed"})
    assert separated.status_code == 201
    old = client.get(f"/events/{e['id']}").json()
    new = client.get(f"/events/{separated.json()['id']}").json()
    assert len(old["reports"]) == 1
    assert new["reports"][0]["text"] == b["text"]
    assert old["history"][-1]["action"] == "report_removed_by_split"
    assert new["history"][-1]["action"] == "report_split"


def test_categories_and_places_are_not_merged(client):
    e = approve(client, report(client))
    b = report(client, location="Shelter B")
    assert client.get(f"/reports/{b['id']}/suggestions").json()["candidates"] == []
    d = report(client, need="diapers")
    assert client.post(f"/reports/{d['id']}/link", json={"event_id": e["id"], "reason": "Wrong category"}).status_code == 422


def test_time_window_and_unknown_time(client):
    approve(client, report(client))
    later = report(client, reported_at="2026-09-04T10:00:00Z")
    assert client.get(f"/reports/{later['id']}/suggestions").json()["candidates"] == []
    unknown = report(client, reported_at=None)
    assert "unknown_event_time" in client.get(f"/reports/{unknown['id']}/suggestions").json()["candidates"][0]["flags"]


def test_validation_and_duplicate_approval(client):
    r = report(client)
    approve(client, r)
    assert client.post(f"/reports/{r['id']}/new-event", json={"reason": "Second approval"}).status_code == 409
    data = {k: v for k, v in r.items() if k not in ["id", "received_at", "event_id", "review_version"]}
    for patch in [{"text": " "}, {"quantity": -1}, {"reported_at": "2026-09-01T10:00:00"}, {"unit": None}, {"reported_at": "2999-01-01T10:00:00Z"}]:
        assert client.post("/reports", json=data | patch).status_code == 422


def test_greek_source_is_preserved(client):
    text = "Χρειαζόμαστε νερό στο καταφύγιο Α."
    r = report(client, text=text, language="el")
    e = approve(client, r)
    assert client.get(f"/events/{e['id']}").json()["reports"][0]["text"] == text


def test_persistence(tmp_path):
    path = str(tmp_path / "persistent.db")
    with TestClient(create_app(path, {TOKEN: "reviewer"})) as c:
        c.headers["Authorization"] = f"Bearer {TOKEN}"
        r = report(c)
    with TestClient(create_app(path, {TOKEN: "reviewer"})) as c:
        c.headers["Authorization"] = f"Bearer {TOKEN}"
        assert c.get("/reports").json()[0]["id"] == r["id"]


def test_missing_credentials_fail_closed(tmp_path):
    with pytest.raises(RuntimeError):
        create_app(str(tmp_path / "none.db"), {})


def test_dashboard_assets_and_data_access(client):
    client.headers.pop('Authorization')
    response = client.get('/')
    assert response.status_code == 200
    assert 'Koordinasyon masası' in response.text
    assert 'frame-ancestors' in response.headers['content-security-policy']
    assert response.headers['cache-control'] == 'no-store'
    for path, content_type in [('/static/app.js', 'javascript'), ('/static/style.css', 'text/css'), ('/static/favicon.svg', 'image/svg+xml')]:
        response = client.get(path)
        assert response.status_code == 200
        assert content_type in response.headers['content-type']
        assert TOKEN not in response.text
    assert client.get('/reports').status_code == 401
