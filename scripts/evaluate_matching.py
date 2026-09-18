"""Small synthetic development check, not a held-out benchmark or validation."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.matching import LocalSemanticEncoder, suggest, THRESHOLD


def metrics(rows, field):
    tp = sum(r['expected'] and r[field] for r in rows)
    fp = sum(not r['expected'] and r[field] for r in rows)
    fn = sum(r['expected'] and not r[field] for r in rows)
    tn = sum(not r['expected'] and not r[field] for r in rows)
    return dict(n=len(rows), tp=tp, fp=fp, fn=fn, tn=tn,
                precision=round(tp/(tp+fp), 4) if tp+fp else None,
                recall=round(tp/(tp+fn), 4) if tp+fn else None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cases', default='evaluation/cases.json')
    parser.add_argument('--output', default='evaluation/results.json')
    args = parser.parse_args()
    raw = Path(args.cases).read_bytes()
    cases = json.loads(raw)
    encoder = LocalSemanticEncoder()
    rows = []
    for case in cases:
        base = dict(event_id=None, quantity=None, unit=None, reported_at='2026-09-01T10:00:00+00:00')
        source = base | dict(id='source', text=case['a'], location=case['location_a'], need=case['need_a'])
        query = base | dict(id='query', text=case['b'], location=case['location_b'], need=case['need_b'], reported_at=case.get('time_b', base['reported_at']))
        event = dict(id='event', status='open', location=source['location'], need=source['need'])
        groups = [(event, [source])]
        baseline = suggest(query, groups)
        semantic = suggest(query, groups, encoder)
        if semantic['matching']['warning']:
            raise RuntimeError('Inference failed; refusing to save misleading semantic results')
        candidates = semantic['candidates']
        rows.append(dict(id=case['id'], language_pair=case['language_pair'], expected=case['expected'],
                         baseline=bool(baseline['candidates']), semantic_union=bool(candidates),
                         similarity=candidates[0]['similarity'] if candidates else None,
                         flags=candidates[0]['flags'] if candidates else [], reason=case['reason']))
    by_language = defaultdict(list)
    for r in rows:
        by_language[r['language_pair']].append(r)
    result = dict(created_at=datetime.now(timezone.utc).isoformat(),
                  kind='synthetic-development-check-not-held-out', labels='author-defined; no independent or native-speaker review',
                  model=encoder.metadata, threshold=THRESHOLD,
                  dataset_sha256=hashlib.sha256(raw).hexdigest(),
                  overall={f: metrics(rows, f) for f in ['baseline', 'semantic_union']},
                  by_language_pair={k: {f: metrics(v, f) for f in ['baseline','semantic_union']} for k,v in by_language.items()},
                  cases=rows)
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result['overall'], indent=2))
    print('False candidate IDs:', [r['id'] for r in rows if r['semantic_union'] and not r['expected']])


if __name__ == '__main__':
    main()
