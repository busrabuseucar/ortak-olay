"""Run the proposal's workflow against the local API using synthetic data only."""
import json
import os
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8000"
TOKEN = os.environ["ORTAK_DEMO_TOKEN"]


def call(method, path, payload=None):
    req = Request(BASE + path, data=json.dumps(payload).encode() if payload is not None else None,
                  headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}, method=method)
    with urlopen(req, timeout=10) as response:
        return json.load(response)


def report(text, language="tr", need="water", quantity=None, time="10:00"):
    return call("POST", "/reports", dict(text=text, language=language, need=need, quantity=quantity,
        unit="people" if quantity is not None else None, location="Shelter A", source="synthetic-demo",
        reported_at=f"2026-09-01T{time}:00Z"))


first = report("Barınak A: 20 kişinin suya ihtiyacı var.", quantity=20)
water = call("POST", f"/reports/{first['id']}/new-event", {"reason": "Exercise location checked"})
second = report("Shelter A: 30 people need water.", "en", quantity=30, time="10:10")
print("Quantity conflict:", json.dumps(call("GET", f"/reports/{second['id']}/suggestions"), ensure_ascii=False))
call("POST", f"/reports/{second['id']}/link", {"event_id": water["id"], "reason": "Same group confirmed in exercise"})
delivery = report("Water delivered; diapers still needed.", "en", time="10:40")
water = call("POST", f"/reports/{delivery['id']}/link", {"event_id": water["id"], "reason": "Delivery evidence reviewed"})
diaper_report = report(delivery["text"], "en", "diapers", time="10:40")
diapers = call("POST", f"/reports/{diaper_report['id']}/new-event", {"reason": "Separate unfulfilled need"})
call("PATCH", f"/events/{water['id']}/status", dict(status="fulfilled", evidence_report_id=delivery["id"], expected_version=water["version"], reason="Exercise delivery scope confirmed"))
repost = report(first["text"], quantity=20)
print("Old repost:", json.dumps(call("GET", f"/reports/{repost['id']}/suggestions"), ensure_ascii=False))
assert call("GET", f"/events/{water['id']}")["status"] == "fulfilled"
assert call("GET", f"/events/{diapers['id']}")["status"] == "open"
print("PASS: water fulfilled, diapers open, old repost pending human review.")
