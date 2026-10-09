# Development roadmap

Updated 2026-10-09. Application language does not establish implementation status. The existing application remains v0.4; this documentation revision adds no runtime capability.

## Existing foundation

Python/FastAPI, SQLite, authenticated Turkish coordinator interface, immutable source reports, separate need events, reason/evidence-linked status changes, split history, optional multilingual semantic retrieval and manual group/type annotations are implemented. See [README](README.md) for capability limits and [evaluation](evaluation/README.md) for the 18-pair development check.

## Priority 1 - Confirm the coordinator task (pending)

Use the [interview guide](docs/COORDINATOR_RESEARCH_TR.md). Seek three coordinator interviews and two anonymised workflow examples. Recruitment is not secured; these counts are planning targets.

Establish the current tools, decision owner, recurring ambiguity, information required to close a need and burden of entering structured fields. Record contradictory feedback as well as support.

Acceptance: permissioned, anonymised notes; a concrete existing workflow; an explicit keep/change/stop decision and the product changes it supports. If interviews are unavailable, keep the exercise prototype label and report the dependency rather than inventing validation.

## Priority 2 - Make review decisions recoverable (not implemented)

### Linked scope correction

Allow a reviewer to correct group/type after a report is linked without altering its original text. Design the affected report/event transaction first: preserve the old values and reason, detect stale edits, and surface implications for group consistency and earlier status evidence. Simply splitting a report into a new event does not make its scope editable today.

Acceptance: a wrongly classified or grouped linked report can be corrected through the UI; conflicts and affected evidence are explicitly handled; no history is silently erased; another reviewer's stale correction is rejected. The final policy for reopening affected needs must be agreed with coordinators before implementation.

### Persistent candidate rejection and reversible dismissal

Record a rejection against the report-event relationship, with actor, reason and evidence version. Distinguish rejected relationships from irrelevant reports. Provide a reversible way to resolve irrelevant reports out of the pending queue while preserving source/history.

Acceptance: a rejected unchanged suggestion is identifiable after reload; new evidence can trigger explicit reconsideration; dismiss/restore actions are audited; a factual unresolved need is not silently discarded. Confirm this interaction with users.

### Unknown location at intake

Currently location/category are mandatory. Determine whether users need a separate unclassified intake state. Do not substitute the same literal 'unknown' location for every report: it could create false matches.

Acceptance, if approved: unknown identity remains distinct from a confirmed shared location and cannot itself justify matching.

## Priority 3 - Narrow extraction and controlled imports (planned)

Start with one need category, such as water. Add a provider interface for proposed fields and exact source spans, schema validation, unknown values and reviewer correction. Model output must not invoke decision/mutation endpoints. Model selection, cost and data handling are not settled by this plan.

Add CSV preview, row-level validation and explicit import confirmation for synthetic exercise data. Define duplicate-import behavior before claiming reproducibility.

Acceptance: an original message yields editable proposed fields with source support; unsupported values remain unresolved; failed extraction leaves manual entry available; structured facts and extraction corrections are distinguishable in the audit record.

## Priority 4 - Independent evaluation and measured workload (pending)

Follow [the proposed protocol](docs/VALIDATION_PLAN.md). Keep the existing 18 cases as development/regression examples. Freeze new scenario-family partitions before tuning. Evaluate candidate retrieval, extraction, final need decisions and full user workload separately.

Acceptance: independently reviewed labels, frozen test partition, baseline comparisons, error examples and reproducible configuration. Publish null or negative results too. Proposed dataset sizes and the 20% time target are not achieved results and are not a statistical power calculation.

## Priority 5 - Controlled pilot readiness (future)

Only after user evidence and recovery workflows: organization-level authorization, user accounts, token rotation, TLS, request limits, monitoring, backups, retention rules and recovery/load tests. Review source permissions and data minimization with a prospective partner. SQLite and the current token map are local-prototype choices, not a multi-organization deployment design.

Acceptance: an agreed supervised exercise/pilot plan and its technical gates. No partner or field deployment is currently established by this roadmap.

## Portfolio evidence

Publish a short reproducible demo and clear current/planned feature list. Attribute actual contributions and AI assistance accurately. Never turn prototype tests, finalist status or planned roles into claims of operational impact or completed team authorship.
