# Proposed validation protocol

Status: proposed, not executed. The 2026-10-09 application revision introduced planning targets; it did not create a dataset, recruit participants or establish performance.

## Evidence ledger

| Evidence | State |
|---|---|
| Functional API/browser tests | Present in repository; verify a specific commit's CI separately |
| 18 synthetic author-labelled matching pairs | Existing development fixture, not held-out |
| 60 new scenario families | Proposed, not collected or labelled |
| Greek proficient-speaker review | Pending; reviewer not secured |
| Three coordinator interviews / two workflow examples | Proposed recruitment targets |
| Five-person usability study, including two coordinators | Proposed; participants not recruited |
| At least 20% median time reduction without more incorrect merges | Internal decision target, not a result or statistically justified sample-size choice |

## Freeze evidence before tuning

Proposed dataset: 60 scenario families, 20 led by each language (TR/EL/EN), with 3-6 messages per family. 'Family' means a shared underlying incident, including all translations and paraphrases. Use stable family IDs. Split 36 families for development and 24 for test, with 12/8 per primary language. Never split a translation from its parent incident.

Keep the original 18 pairs separately as regression cases; do not relabel them held-out. Independent annotators should not derive gold labels from system suggestions. Two annotators label relevant fields, relationships and need updates, then resolve disagreements and preserve uncertainty. Greek cases need a proficient speaker. Do not fabricate a second reviewer or mark generated text as language-reviewed.

Before test execution, record dataset hash, split manifest, annotation instructions/version, model snapshot, extraction configuration, threshold, code commit and known exclusions. Thresholds are tuned on development only. If test errors drive a change, those cases become development evidence and a fresh test is needed.

## Separate three questions

### A. Candidate retrieval

Compare rules-only retrieval with rules plus semantic retrieval under identical structured inputs and gating. Measure TP/FP/FN/TN, precision and recall; report sample counts and errors per language and scenario. A false candidate is not a human-approved incorrect merge.

Include same-site different groups, location aliases, missing times, incompatible units, stale reposts, negation and partial fulfilment. Add multiple candidate events per query so the evaluation is not limited to isolated pairs. Keep correct, missing and erroneous human annotations distinguishable; do not assume perfect metadata in every case.

### B. Proposed field extraction

After implementation, evaluate each field against independently reviewed labels and source spans. Separate correct extraction, unsupported value, missing value and required human correction. Record model/runtime and failures. Tests for structured scope rules do not establish that text extraction understands groups or hypothetical statements.

### C. Coordinator task and workload

First confirm the real baseline in interviews. The proposed comparison is a searchable chronological list versus the prototype, with identical source information and equivalent translation assistance.

Plan five reviewers, including two coordinators, for formative observation. This small sample cannot prove population-wide benefit or safety. If recruitment is smaller, report actual roles/counts and narrow the claims.

Use different but comparable task sets and counterbalance tool order. Provide equivalent familiarisation. Count all task time, including structured entry, reading, translation, correction and recovery; do not compare pre-filled prototype data with raw-message baseline work. Separately log review-only time if useful, clearly labelled.

For each task record: anonymous participant ID, role, scenario family, tool/order, start/end, completion, approved wrong links, missed/incorrect status updates, corrections, help received, interruptions and comments. Predefine treatment of abandoned tasks; do not remove failures to improve median time.

Primary exploratory target: at least 20% lower median end-to-end time without an increase in incorrect-merge rate relative to baseline. Report the rate denominator, raw counts, paired observations and uncertainty, including other errors; zero observed errors in five people is not evidence of safety. Revisit target feasibility from the real baseline before freezing the study, documenting any change before seeing outcomes.

## Required outputs

- Permissioned workflow findings and a keep/change/stop scope decision.
- Annotation guide, family split manifest and reproducible model/baseline results.
- Failure examples, including negative results and unresolved language dependencies.
- Anonymous task logs and a clear account of sample limitations.
- An updated README that labels implemented features, measured evidence and pending work separately.

Existing audit timestamps record decisions, not task start times; they alone cannot measure review duration. Task instrumentation or an external observation sheet must be added before claiming time savings.
