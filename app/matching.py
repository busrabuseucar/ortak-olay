"""Read-only candidate retrieval. Similarity is not probability or validation."""
from collections import OrderedDict
from datetime import datetime
from importlib.metadata import version
import logging
import math
import os
from threading import Lock
from app.locations import code_conflict
from app.report_scope import NON_FACTUAL, group_conflict, known_group_refs, report_warnings

MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
MODEL_REPO = 'qdrant/paraphrase-multilingual-MiniLM-L12-v2-onnx-Q'
MODEL_REVISION = 'faf4aa4225822f3bc6376869cb1164e8e3feedd0'
THRESHOLD = 0.78  # Provisional development setting; not clinically/operationally calibrated.
logger = logging.getLogger(__name__)


class LocalSemanticEncoder:
    """Optional CPU model. Downloads public model weights, never uploads reports."""
    def __init__(self):
        try:
            from fastembed import TextEmbedding
        except ImportError as exc:
            raise RuntimeError('Install requirements-ai.txt before enabling semantic matching.') from exc
        from huggingface_hub import snapshot_download
        cache_dir = os.getenv('ORTAK_MODEL_CACHE', 'data/models')
        model_path = snapshot_download(MODEL_REPO, revision=MODEL_REVISION, cache_dir=cache_dir,
                                       allow_patterns=['model_optimized.onnx', 'config.json', 'tokenizer.json',
                                                       'tokenizer_config.json', 'special_tokens_map.json'])
        self.model = TextEmbedding(MODEL, specific_model_path=model_path, threads=2, providers=['CPUExecutionProvider'])
        self.cache = OrderedDict()
        self.lock = Lock()
        self.metadata = {'model': MODEL, 'weights_repository': MODEL_REPO, 'weights_revision': MODEL_REVISION, 'pooling': 'mean', 'onnxruntime_version': version('onnxruntime'), 'numpy_version': version('numpy'), 'runtime': 'fastembed', 'runtime_version': version('fastembed'), 'input_token_limit': 512, 'inference': 'local-cpu'}

    def similarities(self, query, documents):
        import numpy as np
        texts = [query, *documents]
        # Bounded memory cache, with no report text or vector files written to disk.
        with self.lock:
            missing = list(dict.fromkeys(t for t in texts if t not in self.cache))
            fresh = dict(zip(missing, self.model.embed(missing, batch_size=32))) if missing else {}
            vectors = [self.cache[t] if t in self.cache else fresh[t] for t in texts]
            for text, vector in zip(texts, vectors):
                self.cache[text] = vector
                self.cache.move_to_end(text)
            while len(self.cache) > 2048:
                self.cache.popitem(last=False)
        matrix = np.asarray(vectors, dtype=np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        if not np.isfinite(matrix).all() or (norms == 0).any():
            raise ValueError('Invalid embedding output')
        matrix = matrix / norms
        return (matrix[1:] @ matrix[0]).clip(-1, 1).tolist()


def eligible(report, event, linked):
    if report.get('event_id') == event['id'] or report['need'] != event['need'] or not linked:
        return False
    # Never confuse message receipt time with the event's reported time.
    comparable = [r for r in linked if r['reported_at'] and report['reported_at']]
    return not (comparable and len(comparable) == len(linked) and all(
        abs((datetime.fromisoformat(r['reported_at']) - datetime.fromisoformat(report['reported_at'])).total_seconds()) > 86400
        for r in comparable))


def flags_for(report, event, linked):
    flags = []
    if any(r['quantity'] is not None and report['quantity'] is not None and r['unit'] == report['unit'] and r['quantity'] != report['quantity'] for r in linked):
        flags.append('quantity_conflict')
    if any(r['unit'] != report['unit'] for r in linked):
        flags.append('unit_mismatch_or_unknown')
    if not report['reported_at'] or any(not r['reported_at'] for r in linked):
        flags.append('unknown_event_time')
    if any(r['text'] == report['text'] for r in linked):
        flags.append('possible_repost')
    if event['status'] == 'fulfilled':
        flags.append('fulfilled_need_requires_review')
    return flags


def suggest(report, groups, encoder=None, threshold=THRESHOLD, location_guard=True):
    """Return union of baseline candidates and semantic candidates; never mutate data."""
    blocked = report.get('statement_type') in NON_FACTUAL
    groups = [] if blocked else [(e, [r for r in rs if r.get('statement_type') not in NON_FACTUAL]) for e, rs in groups]
    groups = [(e, rs) for e, rs in groups if eligible(report, e, rs)]
    requested = 'semantic' if encoder is not None else 'baseline'
    warning = None
    scores = {}
    if encoder is not None and groups:
        sources = [r for _, rs in groups for r in rs]
        try:
            values = encoder.similarities(report['text'], [r['text'] for r in sources])
            if len(values) != len(sources) or any(not math.isfinite(float(v)) or not -1 <= float(v) <= 1 for v in values):
                raise ValueError('Invalid similarity output')
            scores = {r['id']: float(v) for r, v in zip(sources, values)}
        except Exception:
            # Do not leak report text, paths, credentials or provider exceptions to the UI.
            logger.warning('Semantic inference unavailable; returning labelled baseline results')
            warning = 'semantic_unavailable'
    candidates = []
    excluded = []
    excluded_groups = []
    for event, linked in groups:
        same_location = event['location'].casefold() == report['location'].casefold()
        best = max(linked, key=lambda r: scores.get(r['id'], -2))
        score = scores.get(best['id'])
        semantic_match = score is not None and score >= threshold
        if not same_location and not semantic_match:
            continue
        if group_conflict(report, event, linked):
            excluded_groups.append({'event_id': event['id'], 'group_ref': ', '.join(known_group_refs(event, linked)), 'reason': 'group_ref_conflict'})
            continue
        # Do not let semantic similarity override explicit different site codes.
        # Linked aliases remain evidence of human decisions, not automatic overrides.
        if location_guard and not same_location and code_conflict(report['location'], event['location']):
            excluded.append({'event_id': event['id'], 'location': event['location'], 'reason': 'site_code_conflict'})
            continue
        flags = flags_for(report, event, linked)
        if not report.get('group_ref') or not event.get('group_ref'):
            flags.append('group_unknown')
        if report.get('statement_type', 'unknown') == 'unknown' or any(r.get('statement_type', 'unknown') == 'unknown' for r in linked):
            flags.append('statement_type_unknown')
        if not same_location:
            flags.append('location_unverified')
        reasons = ['same_need_category']
        if same_location:
            reasons.append('same_location_label')
        if semantic_match:
            reasons.append('semantic_similarity')
        candidates.append({
            'event_id': event['id'], 'status': event['status'],
            'method': 'baseline+semantic-v1' if same_location and semantic_match else ('semantic-v1' if semantic_match else 'structured-baseline-v1'),
            'evidence_report_ids': [r['id'] for r in linked], 'reasons': reasons, 'flags': flags,
            'similarity': round(score, 4) if score is not None else None,
            'semantic_evidence_report_id': best['id'] if score is not None else None,
        })
    if encoder is not None:
        candidates.sort(key=lambda c: (c['similarity'] if c['similarity'] is not None else -2), reverse=True)
    return {
        'report_id': report['id'], 'candidates': candidates, 'automatic_linking': False,
        'matching': {'requested': requested, 'active': 'baseline' if warning or encoder is None else 'semantic',
                     'warning': warning, 'threshold': threshold if encoder is not None else None,
                     'blocked_reason': 'non_factual_report' if blocked else None, 'report_warnings': report_warnings(report),
                     'excluded_groups': excluded_groups, 'location_guard': 'site-code-v1' if location_guard else None, 'excluded_locations': excluded,
                     'score_is_probability': False, 'model': getattr(encoder, 'metadata', None)},
    }
