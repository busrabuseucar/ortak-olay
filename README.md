# Ortak Olay

Human-reviewed disaster needs tracking across Turkish, Greek and English reports.

**Status: v0.2 coordinator prototype for synthetic exercises.** This repository implements the review workflow behind the Greece–Türkiye Hackathon proposal. It is not a deployed emergency service. The matching component is an explicit structured baseline, not a trained AI model. A Turkish coordinator dashboard is included. Free-text multilingual extraction remains a future milestone.

## What works

- Persist original reports, source labels, language, event time and receipt time in SQLite.
- Suggest potentially related needs by manually entered location and need category, with a 24-hour event-time filter when times are known.
- Display quantity disagreements, incompatible units, missing timestamps and possible verbatim reposts.
- Require an authenticated reviewer to create an event, link a report, split a mistaken grouping or change a need's status.
- Keep water, diapers and other categories separate. Linking a delivery report does not itself close a need.
- Record reviewer identity, reason, evidence and status history. Reject stale status updates using version checks.
- Use the responsive coordinator interface at `/` to add reports, compare sources, approve links, split mistakes and update status with evidence.
- Explore the API through `/docs` and run a repeatable synthetic walkthrough.

## Quick start

Python 3.12 was used for verification. From this directory:

```sh
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```sh
source .venv/bin/activate
```

Then:

```sh
python -m pip install -r requirements.txt
python scripts/run_local.py
```

The local launcher generates a temporary reviewer token and prints it in your terminal. Open **http://127.0.0.1:8000**, paste that token in the login screen, and select **Oturumu aç**. The token is held in memory only; refreshing the page requires login again. For API exploration, use `/docs` and **Authorize**. It changes on restart. The SQLite data persists in `data/ortak.db`. The launcher binds only to loopback and does not publish the service online.

To run the synthetic walkthrough, keep the server running and open a second terminal in this directory. Activate the same virtual environment. Use the token printed by the launcher:

```powershell
$env:ORTAK_DEMO_TOKEN = "PASTE_LOCAL_TOKEN"
python scripts/demo.py
```

macOS/Linux:

```sh
export ORTAK_DEMO_TOKEN='PASTE_LOCAL_TOKEN'
python scripts/demo.py
```

The walkthrough adds five reports. Running it again adds a new exercise; it never deletes existing records. Use a different `ORTAK_DB` path for a fresh exercise.

## Demonstrated workflow

1. A Turkish report states that 20 people at Shelter A need water. A reviewer creates a water event.
2. An English report says 30 people. The baseline flags the disagreement; a reviewer chooses to link it.
3. A delivery message reports water delivered and diapers still needed. Separate structured reports represent these two needs while preserving the same original message.
4. The reviewer closes only water, with linked evidence and a reason. Diapers stay open.
5. The original water message is posted again. It is flagged as a possible repost; the water event stays closed until a human decides otherwise.

Location labels and categories are currently entered by the reviewer. Identical structured labels allow reports in different languages to be grouped, but this is **not semantic translation or multilingual NLP**. The Greek example in tests is synthetic and still needs review by a proficient speaker before use in an evaluation dataset.

## Tests

```sh
python -m pytest -q
```

The suite covers the application scenario, access control, status conflicts, evidence constraints, split history, category separation, time windows, validation, Greek text preservation and persistence. Passing these functional tests does not measure matching precision, clinical outcomes or disaster-response impact.

The optional browser regression starts an isolated local server and temporary database. It exercises login, report creation, conflicts, linking, delivery status, splitting, stale decisions, safe text rendering, mobile layout, validation and logout through the interface:

```sh
python -m pip install -r requirements-browser.txt
python -m playwright install chromium
python -m pytest -q browser_tests
```

Both suites run in GitHub Actions. The browser dependency is used only for testing; it is not required to run the application.

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/reports` | Submit one structured need report |
| GET | `/reports?pending=true` | Review unlinked reports |
| GET | `/reports/{id}/suggestions` | Inspect baseline candidates and flags |
| POST | `/reports/{id}/new-event` | Approve a separate need event |
| POST | `/reports/{id}/link` | Link a report after review |
| POST | `/reports/{id}/split` | Move a linked report into a new event |
| GET | `/events` | List events |
| GET | `/events/{id}` | View reports, status and history |
| PATCH | `/events/{id}/status` | Change status with evidence and version |

All data endpoints require a bearer token. `/health` and API schema documentation are public locally. `quantity` and `unit` must be entered together or both omitted. Each report belongs to at most one event. One message covering several needs is represented as several reports carrying the same source text.

## Data and decisions

- Original text is immutable through the API. Mistaken links can be split with an audit trail.
- An event represents a location and one need category. Quantities remain source claims; the prototype never silently selects a single true quantity.
- Reviewers may link different location labels when they confirm an alias; matching only suggests exact labels, ignoring case.
- Splitting creates an open event. The previous event's status remains unchanged and its historical decisions remain visible, even if it has no remaining reports.
- Audit records are append-only through this API, not cryptographically tamper-proof. A database administrator can modify the database.
- Reviewer tokens identify accounts by server configuration; there is no registration, role hierarchy, organizational isolation or password recovery yet.

## Next milestones

See [ROADMAP.md](ROADMAP.md). The coordinator interface now connects incoming reports, event details and review decisions. Next, add source-linked extraction and multilingual semantic matching, compare them against this baseline, and validate the workflow with a coordinator.

## Team

Planned project responsibilities from the application:

- Büşra Buse Uçar: project lead, backend and data flow.
- Aliyenur Bulduk: applied AI and application integration.
- Sıla Yıldız: needs categories and evaluation cases.
- Şeyma Öksüzoğlu: product design and review interface.

These are planned responsibilities, not claims that all members authored the current implementation. This initial backend was prepared with AI assistance and needs team review before adopting it as maintained code.

## Development references

- [FastAPI testing documentation](https://fastapi.tiangolo.com/tutorial/testing/)
- [FastAPI security documentation](https://fastapi.tiangolo.com/tutorial/security/first-steps/)

No open-source license has been selected yet. Agree on licensing and team ownership before inviting external reuse.
