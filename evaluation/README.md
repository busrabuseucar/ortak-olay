# Matching development check

This is a **small synthetic development fixture**, not a held-out benchmark, user study or operational validation. The 18 cases and their expected labels were authored while implementing the feature. Nine pairs are intended to belong to the same need event; nine are intended to stay separate. Greek text and all labels still require independent review. No threshold was tuned against these results: the provisional cosine threshold was set to 0.78 before the first run.

## Reproduction

From the repository root, in the application's virtual environment:

```sh
python -m pip install -r requirements-ai.txt
python scripts/evaluate_matching.py
```

This loads the actual model and writes `evaluation/results.json`; it neither starts the API nor changes its database. The output records the dataset SHA-256, model snapshot revision, FastEmbed/ONNX Runtime/NumPy versions, threshold, case-level outcomes and language-pair counts. Timestamps vary on reruns. Backend contract tests use a deterministic test encoder and do not claim to test model quality. CI runs those tests without downloading weights.

Model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Weights: `qdrant/paraphrase-multilingual-MiniLM-L12-v2-onnx-Q`, snapshot `faf4aa4225822f3bc6376869cb1164e8e3feedd0`. FastEmbed 0.8.0 uses mean pooling. The output has 384 dimensions; input is truncated to 512 tokens. The snapshot is pinned in `app/matching.py`, but transitive numerical-library versions can still differ across machines; the observed versions are recorded in results.

Provider references: [FastEmbed supported models](https://qdrant.github.io/fastembed/examples/Supported_Models/) and [quantized model repository](https://huggingface.co/qdrant/paraphrase-multilingual-MiniLM-L12-v2-onnx-Q).

## Observed development results

| Candidate retrieval | True positives | False positives | False negatives | True negatives | Precision | Recall |
|---|---:|---:|---:|---:|---:|---:|
| Structured baseline | 4 | 2 | 5 | 7 | 0.667 | 0.444 |
| Baseline plus semantic | 7 | 5 | 2 | 4 | 0.583 | 0.778 |

Here a positive prediction means an **event was suggested for review**, not automatically merged. Precision is intended matches divided by all suggested pairs; recall is suggested intended matches divided by nine intended matches. These metrics describe this fixture only. Different language-pair groups contain just 2–5 cases and must not be used to rank language performance.

The extra coverage comes with extra false candidates. Similar requests from different shelters score highly; the UI marks different location labels as unverified. Both approaches can also suggest separate households under one broad location label or a hypothetical statement submitted as a real report. Quantity conflicts and delivery updates can legitimately refer to the same event and must not automatically close or split it. Exact negation understanding is not implemented or established by this fixture.

Examples of false candidates are `en-en-other-shelter`, `en-el-other-shelter`, `tr-tr-distinct-groups`, `tr-en-hypothetical`, and `el-el-other-site`. Inspect their texts in `cases.json` and scores in `results.json`. The two missed intended matches remain in the results; they are not removed to improve the summary.

## Limits and next evidence

All cases are short and manually structured. They do not establish robustness to long reports, dialects, spelling errors, adversarial text, noisy location fields or missing timestamps. A same-site candidate can have low semantic similarity and still appear because the design preserves baseline candidates. Time/category gating occurs before scoring. Location warnings do not prove two places are distinct or equivalent.

Keep semantic mode opt-in. Collect independently labelled scenarios with native-speaker review, partition by scenario family before tuning, evaluate on untouched cases, and record coordinator corrections. Prioritize location identity, negation and source-time handling before any controlled pilot. No disaster-response impact, lives saved, user approval or field deployment is claimed.
