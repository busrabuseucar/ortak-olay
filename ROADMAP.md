# Development roadmap

## Completed foundation

Structured report API, SQLite persistence, human decisions, per-need status, evidence links, audit history, rule-based matching baseline and a synthetic scenario test suite. A responsive Turkish coordinator dashboard now serves from `/` and connects to the authenticated API. Reviewer-entered group/type annotations, audited pre-link corrections and additive legacy migration are implemented. Explicit non-factual types cannot become needs, and conflicting known groups cannot be linked. Unknown annotations remain uncertain.

## Milestone 1 — Coordinator interface implemented, user validation pending

Incoming-report, event-detail and review-decision views are implemented. Show original language and source text beside any future extraction. Surface quantity disagreements, unknown timestamps and status evidence. Preserve decisions across restarts. Test keyboard operation, errors, stale version conflicts, linking and splitting with a complete exercise.

Acceptance: a reviewer completes the five-message scenario without invoking API endpoints manually. Record completion time and corrections without inventing performance improvements.

## Milestone 2 — Local semantic retrieval implemented; independent evaluation pending

Implemented: optional local multilingual embeddings, source-linked similarity scores, explicit fallback, and an 18-pair synthetic development comparison in `evaluation/`. A subsequent narrow site-code guard removes three known false candidates without losing intended matches in that fixture. The guard was designed from those failures, so independent evaluation is still pending; default matching remains the baseline.

Next: validate the added annotation burden and correction workflow with a coordinator; support correction of linked scope before considering a pilot. Then define a provider interface that returns extracted fields and exact source spans. Unknown facts must remain unknown. Improve location disambiguation and compare semantic retrieval with the retained structured baseline. Do not let model outputs call mutation endpoints or approve decisions.

Build independently labelled TR/EL/EN exercise cases, reviewed by appropriate speakers. Partition by scenario family before tuning so reposts and translations do not leak across partitions. Include distinct shelters with similar names, different units, conflicting quantities, old reposts, negation and partial fulfilment. Report sample counts, precision, recall and false merges by language and scenario. Do not treat a small synthetic evaluation as real-world validation.

Acceptance: reproducible held-out results for both the baseline and candidate model, with error examples, thresholds and model version recorded. No numerical target is claimed as achieved.

## Milestone 3 — User evidence

Ask a disaster-response coordinator to describe a real workflow using anonymized or synthetic examples. Establish how they decide whether a report is a repeat, an update or a different group; which information they need to close a request; and how mistakes are corrected. Obtain permission before documenting their feedback.

Acceptance: a documented workflow, concrete corrections to the prototype, and a supervised usability exercise. Never write a planned interview as a completed interview.

## Milestone 4 — Controlled pilot readiness

Add organization-level authorization, user accounts, token rotation, TLS, request limits, monitoring, backups, retention rules and database migrations. Review source permissions and data minimization with the pilot organization. Perform load and recovery tests with synthetic data before a supervised pilot. SQLite and the current token map are local-prototype choices, not a multi-organization deployment design.

## Portfolio evidence

Keep commits attributable to the actual author/reviewer, document AI assistance accurately, record a short working demo, publish repeatable setup instructions and explain known limitations. CV claims should state implemented and tested functions; field deployments, impact numbers and model accuracy require their own evidence.
