"""Local prototype API. Human decisions with optional pretrained candidate retrieval."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import sqlite3
from typing import Literal
from uuid import uuid4

from app.matching import LocalSemanticEncoder, suggest
from app.migrations import migrate
from app.report_scope import NON_FACTUAL, group_conflict

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Scope(Input):
    group_ref: str | None = Field(default=None, min_length=1, max_length=100)
    statement_type: Literal["unknown", "need", "update", "hypothetical", "general_info"] = "unknown"


class Report(Scope):
    text: str = Field(min_length=1, max_length=5000)
    language: Literal["tr", "el", "en"]
    source: str = Field(min_length=1, max_length=200)
    location: str = Field(min_length=1, max_length=200)
    need: Literal["water", "food", "shelter", "diapers", "other"]
    quantity: int | None = Field(default=None, ge=0, le=1000000, strict=True)
    unit: str | None = Field(default=None, min_length=1, max_length=50)
    reported_at: AwareDatetime | None = None


class Decision(Input):
    reason: str = Field(min_length=3, max_length=1000)


class Review(Scope):
    reason: str = Field(min_length=3, max_length=1000)
    expected_review_version: int = Field(ge=1)


class ReportDecision(Decision):
    expected_review_version: int | None = Field(default=None, ge=1)


class Link(ReportDecision):
    event_id: str = Field(min_length=1)


class Status(Decision):
    status: Literal["open", "in_progress", "fulfilled"]
    evidence_report_id: str = Field(min_length=1)
    expected_version: int = Field(ge=1)


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS events (
 id TEXT PRIMARY KEY, location TEXT NOT NULL, need TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'open', version INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reports (
 id TEXT PRIMARY KEY, text TEXT NOT NULL, language TEXT NOT NULL,
 source TEXT NOT NULL, location TEXT NOT NULL, need TEXT NOT NULL,
 quantity INTEGER, unit TEXT, reported_at TEXT, received_at TEXT NOT NULL,
 event_id TEXT REFERENCES events(id)
);
CREATE TABLE IF NOT EXISTS audit (
 sequence INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
 actor TEXT NOT NULL, action TEXT NOT NULL, report_id TEXT, event_id TEXT,
 details TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS reports_event ON reports(event_id);
"""


def now():
    return datetime.now(timezone.utc).isoformat()


def create_app(db_path=None, reviewers=None, encoder=None):
    mode = os.getenv("ORTAK_MATCHER", "baseline")
    if mode not in {"baseline", "semantic"}:
        raise RuntimeError("ORTAK_MATCHER must be baseline or semantic")
    db_path = db_path or os.getenv("ORTAK_DB", "data/ortak.db")
    reviewers = reviewers if reviewers is not None else json.loads(os.getenv("ORTAK_REVIEWERS", "{}"))
    if not isinstance(reviewers, dict) or not reviewers or any(
        not isinstance(k, str) or len(k) < 24 or not isinstance(v, str) or not v.strip()
        for k, v in reviewers.items()
    ):
        raise RuntimeError("Set ORTAK_REVIEWERS to a JSON object mapping secret tokens (24+ chars) to reviewer names.")
    if encoder is None and mode == "semantic":
        encoder = LocalSemanticEncoder()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.executescript(SCHEMA)
        migrate(connection)

    @contextmanager
    def database(write=False):
        connection = sqlite3.connect(db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            if write:
                connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get(connection, table, identifier):
        # Table names originate only from this module, never from requests.
        row = connection.execute(f"SELECT * FROM {table} WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise HTTPException(404, "Record not found")
        return dict(row)

    def log(connection, actor, action, report_id=None, event_id=None, **details):
        connection.execute(
            "INSERT INTO audit(timestamp,actor,action,report_id,event_id,details) VALUES(?,?,?,?,?,?)",
            (now(), actor, action, report_id, event_id, json.dumps(details, ensure_ascii=False)),
        )

    auth = HTTPBearer(auto_error=False)

    def reviewer(credentials: HTTPAuthorizationCredentials | None = Depends(auth)):
        if credentials and credentials.scheme.lower() == "bearer":
            for token, name in reviewers.items():
                if secrets.compare_digest(credentials.credentials.encode(), token.encode()):
                    return name
        raise HTTPException(401, "Valid reviewer token required", headers={"WWW-Authenticate": "Bearer"})

    api = FastAPI(
        title="Ortak Olay", version="0.4.0",
        description="Synthetic-exercise prototype. Structured reports, baseline suggestions and human decisions. Optional local multilingual model for candidate retrieval; no operational validation.",
    )

    static = Path(__file__).resolve().parent / "static"
    api.mount("/static", StaticFiles(directory=static), name="static")

    @api.get("/", include_in_schema=False)
    def dashboard():
        return FileResponse(static / "index.html", headers={"Cache-Control": "no-store"})

    @api.middleware("http")
    async def browser_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        if request.url.path not in ("/docs", "/redoc", "/docs/oauth2-redirect"):
            response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        if not request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @api.get("/health")
    def health():
        return {"status": "ok", "version": "0.4.0", "stage": "local-prototype"}

    @api.post("/reports", status_code=201)
    def add_report(item: Report, actor=Depends(reviewer)):
        if (item.quantity is None) != (item.unit is None):
            raise HTTPException(422, "Quantity and unit must be supplied together")
        if item.reported_at and item.reported_at > datetime.now(timezone.utc):
            raise HTTPException(422, "Reported time must not be in the future")
        data = item.model_dump()
        data["reported_at"] = item.reported_at.astimezone(timezone.utc).isoformat() if item.reported_at else None
        data.update(id=str(uuid4()), received_at=now())
        with database(True) as connection:
            connection.execute(
                "INSERT INTO reports(id,text,language,source,location,need,quantity,unit,reported_at,received_at,group_ref,statement_type) "
                "VALUES(:id,:text,:language,:source,:location,:need,:quantity,:unit,:reported_at,:received_at,:group_ref,:statement_type)", data)
            log(connection, actor, "report_created", report_id=data["id"])
            return get(connection, "reports", data["id"])

    @api.get("/reports")
    def reports(pending: bool = False, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0), actor=Depends(reviewer)):
        with database() as connection:
            sql = "SELECT * FROM reports" + (" WHERE event_id IS NULL" if pending else "")
            return [dict(r) for r in connection.execute(sql + " ORDER BY received_at,id LIMIT ? OFFSET ?", (limit, offset))]

    @api.get("/reports/{report_id}")
    def report_detail(report_id: str, actor=Depends(reviewer)):
        with database() as connection:
            result = get(connection, "reports", report_id)
            result["review_history"] = [dict(r) for r in connection.execute(
                "SELECT * FROM audit WHERE report_id=? AND action='report_reviewed' ORDER BY sequence", (report_id,))]
            return result

    @api.patch("/reports/{report_id}/review")
    def review_report(report_id: str, decision: Review, actor=Depends(reviewer)):
        with database(True) as connection:
            report = get(connection, "reports", report_id)
            if report["event_id"]:
                raise HTTPException(409, "Linked report scope cannot be edited")
            if report["review_version"] != decision.expected_review_version:
                raise HTTPException(409, "Report review changed; refresh before deciding")
            before = {k: report[k] for k in ("group_ref", "statement_type")}
            after = decision.model_dump(include={"group_ref", "statement_type"})
            connection.execute("UPDATE reports SET group_ref=?,statement_type=?,review_version=review_version+1 WHERE id=?",
                               (decision.group_ref, decision.statement_type, report_id))
            log(connection, actor, "report_reviewed", report_id=report_id, before=before, after=after, reason=decision.reason)
            return get(connection, "reports", report_id)

    @api.get("/events")
    def events(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0), actor=Depends(reviewer)):
        with database() as connection:
            return [dict(r) for r in connection.execute("SELECT * FROM events ORDER BY created_at,id LIMIT ? OFFSET ?", (limit, offset))]

    @api.get("/events/{event_id}")
    def event(event_id: str, actor=Depends(reviewer)):
        with database() as connection:
            result = get(connection, "events", event_id)
            result["reports"] = [dict(r) for r in connection.execute("SELECT * FROM reports WHERE event_id=? ORDER BY received_at,id", (event_id,))]
            result["history"] = [dict(r) for r in connection.execute("SELECT * FROM audit WHERE event_id=? ORDER BY sequence", (event_id,))]
            return result

    @api.get("/reports/{report_id}/suggestions")
    def suggestions(report_id: str, actor=Depends(reviewer)):
        with database() as connection:
            report = get(connection, "reports", report_id)
            groups = []
            for row in connection.execute("SELECT * FROM events WHERE need=?", (report["need"],)):
                event = dict(row)
                linked = [dict(r) for r in connection.execute("SELECT * FROM reports WHERE event_id=?", (event["id"],))]
                groups.append((event, linked))
        # Release the database connection before model inference.
        return suggest(report, groups, encoder=encoder)

    def check_review_version(report, decision):
        if decision.expected_review_version is not None and report['review_version'] != decision.expected_review_version:
            raise HTTPException(409, "Report review changed; refresh before deciding")

    def require_factual(report):
        if report['statement_type'] in NON_FACTUAL:
            raise HTTPException(422, "Non-factual reports cannot create or update needs")

    def new_event(connection, report, actor, reason, split=False):
        require_factual(report)
        old = report["event_id"]
        event_id = str(uuid4())
        connection.execute("INSERT INTO events(id,location,need,created_at,group_ref) VALUES(?,?,?,?,?)", (event_id, report["location"], report["need"], now(), report["group_ref"]))
        connection.execute("UPDATE reports SET event_id=? WHERE id=?", (event_id, report["id"]))
        log(connection, actor, "report_split" if split else "event_created", report_id=report["id"], event_id=event_id, previous_event_id=old, reason=reason)
        if old:
            connection.execute("UPDATE events SET version=version+1 WHERE id=?", (old,))
            log(connection, actor, "report_removed_by_split", report_id=report["id"], event_id=old, new_event_id=event_id, reason=reason)
        return get(connection, "events", event_id)

    @api.post("/reports/{report_id}/new-event", status_code=201)
    def approve_new(report_id: str, decision: ReportDecision, actor=Depends(reviewer)):
        with database(True) as connection:
            report = get(connection, "reports", report_id)
            if report["event_id"]:
                raise HTTPException(409, "Report already linked; use split to correct it")
            check_review_version(report, decision)
            return new_event(connection, report, actor, decision.reason)

    @api.post("/reports/{report_id}/link")
    def link(report_id: str, decision: Link, actor=Depends(reviewer)):
        with database(True) as connection:
            report = get(connection, "reports", report_id)
            e = get(connection, "events", decision.event_id)
            require_factual(report)
            check_review_version(report, decision)
            linked = [dict(r) for r in connection.execute("SELECT * FROM reports WHERE event_id=?", (e["id"],))]
            if group_conflict(report, e, linked):
                raise HTTPException(422, "Different group references must remain separate")
            if report["event_id"]:
                raise HTTPException(409, "Report already linked")
            if e["need"] != report["need"]:
                raise HTTPException(422, "Different need categories must remain separate")
            connection.execute("UPDATE reports SET event_id=? WHERE id=?", (e["id"], report_id))
            connection.execute("UPDATE events SET version=version+1 WHERE id=?", (e["id"],))
            log(connection, actor, "report_linked", report_id=report_id, event_id=e["id"], reason=decision.reason)
            return get(connection, "events", e["id"])

    @api.post("/reports/{report_id}/split", status_code=201)
    def split(report_id: str, decision: ReportDecision, actor=Depends(reviewer)):
        with database(True) as connection:
            report = get(connection, "reports", report_id)
            if not report["event_id"]:
                raise HTTPException(409, "Unlinked report; use new-event")
            check_review_version(report, decision)
            return new_event(connection, report, actor, decision.reason, split=True)

    @api.patch("/events/{event_id}/status")
    def change_status(event_id: str, decision: Status, actor=Depends(reviewer)):
        with database(True) as connection:
            e = get(connection, "events", event_id)
            evidence = get(connection, "reports", decision.evidence_report_id)
            require_factual(evidence)
            if evidence["event_id"] != event_id:
                raise HTTPException(422, "Evidence report must be linked to this event")
            if e["version"] != decision.expected_version:
                raise HTTPException(409, "Event changed; refresh before deciding")
            connection.execute("UPDATE events SET status=?,version=version+1 WHERE id=?", (decision.status, event_id))
            log(connection, actor, "status_changed", report_id=evidence["id"], event_id=event_id, before=e["status"], after=decision.status, reason=decision.reason)
            return get(connection, "events", event_id)

    return api
