"""Versioned M2 target aggregation and M8 call bands; no semantic inference."""
import copy
try:
    from . import partial_metrics as old
except ImportError:
    import partial_metrics as old

VERSION = 'v2-five-band-2026-09-14'


def targets(rows):
    declared = rows[0]['metadata'].get('protocol', {}).get('acquisition_targets', [])
    ids = [t.get('id') for t in declared]
    reqs = {r['id'] for r in old.declared_requirements(rows)}
    if any(not isinstance(x, str) or not x for x in ids) or len(ids) != len(set(ids)):
        raise ValueError('预定获取目标ID无效或重复')
    for t in declared:
        if not t.get('description') or not t.get('requirement_refs') or set(t['requirement_refs']) - reqs:
            raise ValueError('获取目标须说明范围并关联预定需求')
    return declared


def aggregate(items):
    scores = [t.get('score') for t in items]
    if any(s is not None and (type(s) is not int or not 1 <= s <= 5) for s in scores):
        raise ValueError('目标分值须为整数1—5或null')
    known = [s for s in scores if s is not None]
    complete = bool(scores) and len(known) == len(scores)
    total = sum(known)
    n = len(scores)
    return dict(target_count=n, assessed_count=len(known), unknown_count=n-len(known),
                not_obtained_count=sum(s in (1, 2) for s in known),
                partial_count=known.count(3), score_sum=total,
                mean=total/n if complete else None,
                band=(2*total+n)//(2*n) if complete else None)


def cost_band(c):
    if type(c) is not int or c < 0:
        raise ValueError('调用数须为非负整数')
    return max(1, 5-(c-1)//2) if c else None


def template(rows):
    compat = copy.deepcopy(rows)
    compat[0]['metadata']['rubric_version'] = old.VERSION
    value = old.template(compat)
    value['rubric_version'] = VERSION
    items = [dict(target_id=t['id'], score=None, initial_state='unknown',
                  final_official_state='unknown', reason='', evidence_refs=[], event_refs=[])
             for t in targets(rows)]
    value['metrics'][1]['observation'] = dict(targets=items, aggregate=aggregate(items))
    obs = value['metrics'][7]['observation']
    obs['total_calls'] = obs['C']['S'] + obs['C']['F']
    return value


def validate(rows, value):
    compat = copy.deepcopy(value)
    for m in compat['metrics']:
        if m['id'] in {'M2', 'M8'}:
            m.update(score=None, status='pending')
        if m['id'] == 'M2':
            m['observation'] = None
    old.validate(rows, compat)
    metrics = {m['id']: m for m in value['metrics']}
    m = metrics['M2']
    obs = m.get('observation')
    if not isinstance(obs, dict) or not isinstance(obs.get('targets'), list):
        raise ValueError('M2须含目标清单')
    items = obs['targets']
    ids = [t.get('target_id') for t in items]
    if len(ids) != len(set(ids)) or set(ids) != {t['id'] for t in targets(rows)}:
        raise ValueError('M2必须完整对应预定目标，不按URL增删目标')
    expected = aggregate(items)
    if obs.get('aggregate') != expected:
        raise ValueError('M2均值、分档或缺口计数不符')
    for t in items:
        s = t.get('score')
        if any(t.get(k) not in old.STATES for k in ('initial_state', 'final_official_state')):
            raise ValueError('目标获取状态无效')
        if s is None:
            continue
        state = 'not_obtained' if s <= 2 else 'partial' if s == 3 else 'obtained'
        if t['final_official_state'] != state or not t.get('reason') or not t.get('evidence_refs') or not t.get('event_refs'):
            raise ValueError('目标评分须有一致的最终状态、理由、事件和原文证据')
        if t['initial_state'] == 'unknown':
            raise ValueError('首次获取未知，不能判定获取路径档位')
        if s == 4 and (t['initial_state'] == 'obtained' or not t.get('recovery_event_refs')):
            raise ValueError('四分须保留初次障碍及官方替代路径事件')
        if s == 5 and t['initial_state'] != 'obtained':
            raise ValueError('五分须直接取得正文')
        if set(t.get('recovery_event_refs', [])) - set(t['event_refs']):
            raise ValueError('恢复事件须列入可校验的event_refs')
    check_score(m, expected['band'])
    m = metrics['M8']
    obs = m.get('observation')
    if not isinstance(obs, dict):
        raise ValueError('M8须保存成本明细')
    c = obs['C']['S'] + obs['C']['F']
    if type(obs.get('total_calls')) is not int or obs['total_calls'] != c:
        raise ValueError('M8总调用数须等于S+F')
    check_score(m, cost_band(c))


def check_score(metric, expected):
    score = metric.get('score')
    if score is None:
        if metric.get('status') == 'scored':
            raise ValueError('scored须有分值')
        return
    if type(score) is not int or score != expected or metric.get('status') != 'scored' or not metric.get('reason'):
        raise ValueError('分值须符合聚合公式/分档，且提供scored状态与理由')
