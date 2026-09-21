"""Conservative within-model paired summaries; no imputation or pooled models."""
import hashlib
import json
import math
from pathlib import Path

R = Path(__file__).resolve().parent


def eligible(row, metric_id):
    if row and row.get('collection_status') == 'technical_attempts_exhausted':
        return None, 'technical_attempts_exhausted'
    if not row or not row.get('collected'):
        return None, 'not_collected'
    if not row.get('assessed'):
        return None, 'not_assessed'
    if not row.get('gate_passed'):
        return None, 'structural_gate_failed'
    if row.get('quote_issues') != 0:
        return None, 'quote_audit_not_clean'
    metric = next((m for m in row.get('metrics', []) if m['id'] == metric_id), None)
    if not metric:
        return None, 'metric_missing'
    if metric.get('status') in ('not_applicable', 'blocked', 'incomplete_inputs'):
        return None, metric['status']
    lo, hi, score = metric.get('lower'), metric.get('upper'), metric.get('score')
    if lo is None and hi is None:
        lo = hi = score
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (lo, hi)):
        return None, 'missing_or_invalid_numeric_bounds'
    maximum = 100 if metric_id == 'M11' else 5
    if not 0 <= lo <= hi <= maximum:
        return None, 'out_of_scale_bounds'
    return [lo, hi], None


def build(data, task_ids):
    tasks = [t for t in task_ids if t != 'G']
    assert len(tasks) == 25 and len(set(tasks)) == 25
    out = {'scope': {'tasks': tasks, 'exclude_tasks': ['G'], 'note':
        'Within-model complete eligible pairs only. Bounds are evidence bounds, not statistical confidence intervals. Structural and quote checks are not full semantic validation. Incomplete pairs can cause selection bias; these are provisional descriptive summaries.'}, 'models': {}}
    for model in sorted({row['model'] for row in data['rows']}):
        by = {(row['task'], row['ecosystem']): row for row in data['rows'] if row['model'] == model}
        metrics = {}
        for number in range(1, 12):
            metric_id = f'M{number}'
            pairs, excluded = [], []
            for task in tasks:
                a, b = by.get((task, 'cann')), by.get((task, 'cuda'))
                ca, ce = eligible(a, metric_id)
                nv, ne = eligible(b, metric_id)
                if ce or ne:
                    excluded.append({'task': task, 'cann_reason': ce, 'cuda_reason': ne})
                else:
                    pairs.append({'task': task, 'cann_run': a['run_id'], 'cuda_run': b['run_id'],
                                  'cann': ca, 'cuda': nv, 'difference_bounds': [ca[0]-nv[1], ca[1]-nv[0]]})
            def mean(key):
                return [sum(p[key][i] for p in pairs)/len(pairs) for i in (0, 1)] if pairs else None
            assert len(pairs) + len(excluded) == 25
            metrics[metric_id] = {'n': len(pairs), 'pairs': pairs, 'excluded_tasks': excluded,
                'cann_mean': mean('cann'), 'cuda_mean': mean('cuda'), 'difference_bounds': mean('difference_bounds')}
        out['models'][model] = metrics
    return out


if __name__ == '__main__':
    raw = (R/'results.json').read_bytes()
    output = build(json.loads(raw), json.loads((R/'tasks.json').read_text())['tasks'])
    output['source_results_sha256'] = hashlib.sha256(raw).hexdigest()
    (R/'paired-summary.json').write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n')
