# Ortak Olay

Human-reviewed disaster needs tracking across Turkish, Greek and English reports.

**Status: v0.5 coordinator prototype with reviewer-entered report scope and optional local semantic retrieval.** This repository implements the review workflow behind the Greece–Türkiye Hackathon proposal. It is not a deployed emergency service. Matching defaults to a structured baseline. An optional pretrained multilingual model adds candidates for human review; it has not been trained on disaster reports. A Turkish coordinator dashboard is included. Free-text multilingual extraction remains a future milestone.

## Start with the coordinator's task

A new message can be a new need, an old request reposted, or an update to a known need. Ortak Olay brings the original sources and candidate relationships together so a human can decide and leave an accountable history.

The initial setting is a disaster-response exercise involving basic supplies and shelter reports. Whether this workflow reduces a real coordinator's workload remains unverified. Manual entry and correction time must count when measuring any benefit.

### Current capability versus planned work

| Capability | Current state |
|---|---|
| Report entry, source preservation, per-need status and audited decisions | Implemented local prototype; follow the walkthrough below |
| Multilingual candidate retrieval | Optional pretrained local embeddings; structured baseline remains the default |
| Free-text extraction and evidence spans | Planned; location/category and other structured facts are currently entered by the reviewer |
| Missing information | Quantity/unit, event time and group can be unknown; location and need category are required. Missing location is not yet a supported intake workflow |
| Correct report scope | Group/type corrections are audited; linked corrections require explicit detachment and mark the old need for review |
| Reject a suggested relationship | Reasoned rejection/restore is persisted per report-event pair; evidence changes invalidate prior rejection |
| Resolve irrelevant messages | Explicit non-factual types block need decisions, but remain in the pending queue; reversible dismissal is planned |
| CSV exercise imports | Planned; manual entry and the scripted synthetic walkthrough exist |
| Independent evaluation and coordinator study | Pending; the existing 18-pair check is a development fixture |
| Public operational service | Not deployed; local exercise prototype only |

The [development check](evaluation/README.md) reports both useful matches and errors; it does not establish time savings or operational accuracy. Existing functional tests verify application behavior, not user benefit.

### Next work and evidence

1. [Coordinator interview and recording guide (Turkish)](docs/COORDINATOR_RESEARCH_TR.md): establish the current workflow before extending scope.
2. [Prioritized delivery roadmap](ROADMAP.md): validate recovery workflows with coordinators before broader automation.
3. [Proposed evaluation protocol](docs/VALIDATION_PLAN.md): separate development fixtures, independent matching tests and user tasks.

These documents contain plans and blank recording templates, not completed interviews, recruited partners or achieved targets. No working-demo video or screenshot is linked yet; the executable walkthrough and setup below are the current demonstration materials.

## What works

- Persist original reports, source labels, language, event time and receipt time in SQLite. Record optional group references and reviewer-assigned message types.
- Exclude explicitly hypothetical/general-information reports from suggestions and need decisions. Prevent links between explicitly conflicting group references, including references in already linked sources.
- Correct report scope with reason, version checks and visible audit history; linked corrections explicitly detach and flag the old event for review.
- Suggest potentially related needs by manually entered location and need category, with a 24-hour event-time filter when times are known. Optionally add semantic candidates across Turkish, English and Greek, with source-linked similarity and different-location warnings.
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

Location labels and categories are still entered by the reviewer. The default baseline compares structured labels; optional semantic retrieval compares original text using a pretrained multilingual model. Neither mode extracts fields automatically or verifies facts. Greek examples are synthetic and have not been reviewed by a proficient speaker.

## Reviewer-entered group and message scope

These fields are **human annotations**, not extracted or verified by AI:

| Field | Values / meaning |
|---|---|
| `group_ref` | Optional shared group/tent identifier, e.g. `tent-12`. Use the same identifier across languages; only case and whitespace are normalized. No translation or group identity inference occurs. |
| `statement_type` | `unknown` (default), `need`, `update`, `hypothetical`, or `general_info`. `need` and `update` describe the coordinator's reading, not independently verified facts. |

Reports marked `hypothetical` or `general_info` remain available for inspection but cannot suggest events, create needs, link to them, or act as status evidence. The UI hides the need decision form. They remain in the unlinked-report queue; archiving is not implemented. If the annotation was wrong, correct it in **Rapor değerlendirmesini düzelt** with a reason before linking.

An event inherits its founding report's group reference. A known incoming group must not contradict the event's reference or any linked source's known reference. Such candidates appear as excluded with a reason, and the API rejects a manual link too. Unknown scope is not inferred or silently filled: it produces warnings and still permits a human decision. Group references are intended to be consistently assigned within the operating context; the prototype has no global group registry.

`PATCH /reports/{id}/review` updates group/type with a reason and `expected_review_version`. For a linked report, also supply `detach_linked: true` and `expected_event_version`. This explicitly removes the link, preserves the source and old decisions, and marks the former event `review_required`. The prior status and event group label are retained as historical assertions, not silently rewritten. The report returns to the unlinked queue. This conservative exercise workflow requires coordinator validation; it is not an agreed field procedure.

Events requiring review are visibly flagged and excluded from the completed counter. A new status decision using currently linked factual evidence, a reason and the current event version clears the flag. An empty event cannot be reaffirmed without new linked evidence. Splitting also marks the former event for review. This does not automatically reopen fulfilled needs.

`POST /reports/{id}/candidate-decision` records `reject` or `restore` for an unlinked report and event. Supply the reason plus `expected_review_version`, `expected_event_version` and `expected_decision_version` (0 for the first decision). Active rejection hides that candidate from suggestions and prevents manual linking until restored. Changes to report scope or event evidence/version make the rejection stale, visible as such, and allow reconsideration; old audit entries remain. Rejection applies to one relationship, not to the report itself. Reversible report dismissal remains unimplemented.

`GET /reports/{id}` includes scope and candidate decision history. Concurrent stale edits return 409; reload before deciding. Original text, location and need category are not editable through the scope endpoint. Event group labels are not automatically inferred from corrected sources.

Existing SQLite databases receive additive columns on startup. Original text, links, status, event versions and audit history remain intact; old reports start with unknown type and no group. The migration is repeatable and tested on a legacy database. There is no automatic backfill or classification of old records.

The original 18-case evaluation supplies none of these new human annotations. Its matching counts therefore remain unchanged. Functional scope tests demonstrate rule enforcement when annotations are supplied; they do **not** establish text understanding or improve measured model accuracy.

## Optional local AI matching

Install and launch from the same virtual environment:

```sh
python -m pip install -r requirements-ai.txt
python scripts/run_local.py --semantic
```

The first launch downloads roughly 220 MB of public model weights from Hugging Face. Reports are encoded locally on CPU; their text is not submitted to a model service. Model files use `data/models` by default (`ORTAK_MODEL_CACHE` overrides it). After downloading, `HF_HUB_OFFLINE=1` enables cached-only loading. A missing model or failed download stops semantic startup explicitly; start without `--semantic` for the baseline. Inference errors after startup produce clearly labelled baseline fallback results.

The model is `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, using FastEmbed 0.8.0, mean pooling, and a pinned quantized ONNX snapshot. This uses a pretrained model; it is not a new model trained by the team. See [evaluation/README.md](evaluation/README.md) for provenance and limitations.

- Candidates start as the union of the baseline and cosine similarity at least **0.78**, then a narrow site-code conflict check removes contradictory labels from suggestions. This threshold is a provisional development choice, not a calibrated probability.
- Need categories must match. Events with only known source times all more than 24 hours away are excluded. If any source time is unknown, the event remains eligible with a warning. All sources of an eligible event participate in scoring, so inspect the timestamp of the best-matching source too.
- Different location labels are **not** resolved or geocoded. A conservative parser checks complete labels such as `Shelter A`, `Barınak B`, `Σχολείο Β`, or a bare code `A`. Conflicting letter/integer codes within the same site type (or with an unspecified type) are excluded from suggestions and shown separately with a reason. Compatible codes never prove identity. Unrecognized labels retain the existing location warning. Manual review and linking remain possible; previously approved aliases are not learned automatically.
- The model sees at most the first **512 tokens**. Full original text remains visible. Negation, hypotheticals, delivery status and quantity conflicts require human inspection.
- No model output can link reports, close needs or dispatch resources. Embeddings are held in a bounded memory cache only; original reports still persist in SQLite.
- Every suggestion currently scans eligible events and their sources. There is no vector index or proven large-dataset performance yet.

Reproduce the real-model development check (does not touch the application database):

```sh
python scripts/evaluate_matching.py
```

On the same 18 synthetic, author-labelled pairs, the baseline retrieves 4 of 9 intended matches with 2 false candidates. Semantic-plus-baseline without the location check retrieves 7 of 9 with 5 false candidates; with the check it retains those 7 matches and yields 2 false candidates. The location check was developed after inspecting these errors, so this is a regression measurement on known cases, not an independent evaluation. It is **not evidence of operational accuracy**. The feature remains opt-in. Full case-level results and per-language-pair counts are committed in `evaluation/results.json`.

## Tests

```sh
python -m pytest -q
```

The suite covers the application scenario, access control, status conflicts, evidence constraints, split history, category separation, time windows, validation, Greek text preservation, scope rules, audited classification correction, legacy migration and persistence. Passing these functional tests does not measure matching precision, clinical outcomes or disaster-response impact.

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
| GET | `/reports/{id}` | Read report and scope-review history |
| PATCH | `/reports/{id}/review` | Correct scope; explicitly detach linked reports and flag the old event |
| POST | `/reports/{id}/candidate-decision` | Reject or restore a relationship with reason and version guards |
| GET | `/reports/{id}/suggestions` | Inspect candidate methods, source evidence and flags |
| POST | `/reports/{id}/new-event` | Approve a separate need event |
| POST | `/reports/{id}/link` | Link a report after review |
| POST | `/reports/{id}/split` | Move a linked report into a new event |
| GET | `/events` | List events |
| GET | `/events/{id}` | View reports, status and history |
| PATCH | `/events/{id}/status` | Change status with evidence and version |

All data endpoints require a bearer token. `/health` and API schema documentation are public locally. `quantity` and `unit` must be entered together or both omitted. Each report belongs to at most one event. One message covering several needs is represented as several reports carrying the same source text.

## Data and decisions

- Original text is immutable through the API. Mistaken links can be split with an audit trail.
- An event represents a location, one need category and an optional group reference. Quantities remain source claims; the prototype never silently selects a single true quantity.
- Reviewers may link different location labels when they confirm an alias; the baseline suggests exact labels, ignoring case. Semantic mode may suggest different labels, always with a location warning.
- Splitting creates an open event. The previous event's status remains unchanged and its historical decisions remain visible, even if it has no remaining reports.
- Audit records are append-only through this API, not cryptographically tamper-proof. A database administrator can modify the database.
- Reviewer tokens identify accounts by server configuration; there is no registration, role hierarchy, organizational isolation or password recovery yet.

## Next milestones

See [ROADMAP.md](ROADMAP.md). The coordinator interface now connects incoming reports, event details and review decisions. Optional multilingual matching now has a reproducible development comparison. Next, validate the recovery and review workflows with a coordinator, then build source-linked extraction and independently labelled evaluation cases. Scope rules now work with explicit human annotations; automatic group/statement extraction is not implemented.

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

The optional pretrained model is listed under Apache-2.0 by its provider; that does not license this application. No open-source license has been selected yet. Agree on licensing and team ownership before inviting external reuse.
