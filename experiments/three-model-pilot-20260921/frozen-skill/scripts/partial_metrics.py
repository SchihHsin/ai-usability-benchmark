"""Validate confirmed metric structure; semantic judgments remain evidence-based reviews."""
VERSION = 'v2-partial-2026-09-14'
STATES = {'not_obtained', 'partial', 'obtained', 'unknown'}


def declared_requirements(rows):
    return rows[0]['metadata'].get('protocol', {}).get('requirements', [])


def cost_vector(rows, retries=None, no_body=None):
    requests = {r['id']: r for r in rows if r['type'] == 'tool_request'}
    dispatched = {r['request_id'] for r in rows if r['type'] == 'tool_dispatch'}
    def count_ids(ids, roles):
        if ids is None:
            return None
        if not isinstance(ids, list) or any(not isinstance(x, str) for x in ids) or len(ids) != len(set(ids)):
            raise ValueError('成本请求ID须为不重复列表或null')
        if any(x not in dispatched or x not in requests or requests[x]['role'] not in roles for x in ids):
            raise ValueError('成本只能引用已派发的相应工具请求')
        return len(ids)
    return dict(S=sum(requests[x]['role'] == 'search' for x in dispatched),
                F=sum(requests[x]['role'] == 'fetch' for x in dispatched),
                R=count_ids(retries, {'search', 'fetch'}), U=count_ids(no_body, {'fetch'}))


def template(rows):
    version = rows[0]['metadata']['rubric_version']
    value = dict(rubric_version=version, assessor={'id': None, 'method': 'evidence_review'},
                 limitations=['评价尚未完成'], evidence=[], issues=[], requirements=[], metrics=[], overall=None)
    for r in declared_requirements(rows):
        value['requirements'].append(dict(id=r['id'], status='pending', reason='', evidence_refs=[]))
    for i in range(1, 12):
        value['metrics'].append(dict(id=f'M{i}', score=None, status='pending', observation=None,
                                     reason='', requirement_refs=[], evidence_refs=[], event_refs=[]))
    if version == VERSION:
        value['metrics'][1]['observation'] = {'targets': []}
        value['metrics'][7]['observation'] = dict(C=cost_vector(rows), retry_request_ids=None, no_body_fetch_request_ids=None)
        value['metrics'][2]['official_body_observed'] = None
        value['metrics'][9].update(scope='main_solution', applicable_conditions=None, runtime_validation='not_executed')
    return value


def validate(rows, value):
    metrics = value['metrics']
    ids = [m.get('id') for m in metrics]
    if len(ids) != 11 or set(ids) != {f'M{i}' for i in range(1, 12)}:
        raise ValueError('本版评价须包含不重复的M1–M11')
    if value.get('overall') is not None:
        raise ValueError('本版不计算M11综合分')
    declared = declared_requirements(rows)
    req_ids = [r.get('id') for r in declared]
    if any(not isinstance(x, str) or not x for x in req_ids) or len(req_ids) != len(set(req_ids)):
        raise ValueError('预定需求ID缺失或重复')
    assessed_ids = [r.get('id') for r in value['requirements']]
    if len(assessed_ids) != len(set(assessed_ids)) or set(assessed_ids) - set(req_ids):
        raise ValueError('评价需求必须对应执行前清单且不重复')
    for m in metrics:
        score = m.get('score')
        if score is not None:
            if m['id'] not in {'M3', 'M10'} or type(score) is not int or not 1 <= score <= 5:
                raise ValueError('本版仅M3/M10允许整数1—5分')
            if m.get('status') != 'scored' or not str(m.get('reason') or '').strip() or not m.get('evidence_refs'):
                raise ValueError('填分须有scored状态、判定理由和原文证据')
            refs = m.get('requirement_refs')
            if not isinstance(refs, list) or not refs or set(refs) - set(req_ids):
                raise ValueError('填分须关联预定任务需求')
            if not req_ids or set(assessed_ids) != set(req_ids):
                raise ValueError('填分前须逐项整理全部预定需求')
            if any(r.get('status') in {None, 'pending', 'unknown'} or not r.get('reason') or not r.get('evidence_refs') for r in value['requirements']):
                raise ValueError('需求判定尚未完成或缺少证据')
            if m['id'] == 'M3':
                if m.get('official_body_observed') is not True:
                    raise ValueError('未取得相关官方正文时M3不可给低分')
                if any(r.get('importance') not in {'core', 'supplementary'} for r in declared) or not any(r['importance'] == 'core' for r in declared):
                    raise ValueError('M3需执行前确定核心/辅助要求')
                if score == 4 and not any(r['importance'] == 'supplementary' for r in declared):
                    raise ValueError('无预定辅助要求时不能因辅助缺口给M3四分')
            if m['id'] == 'M10':
                if m.get('scope') != 'main_solution' or not m.get('applicable_conditions'):
                    raise ValueError('M10须说明主方案范围及适用条件')
                if m.get('runtime_validation') not in {'not_executed', 'executed'}:
                    raise ValueError('M10运行验证状态须另列')
        elif m.get('status') == 'scored':
            raise ValueError('scored须有分值')
        obs = m.get('observation')
        if m['id'] == 'M2' and obs is not None:
            if not isinstance(obs, dict) or not isinstance(obs.get('targets'), list):
                raise ValueError('M2 observation须含targets列表')
            target_ids = []
            for t in obs['targets']:
                target_ids.append(t.get('target_id'))
                if not t.get('target_id') or any(t.get(k) not in STATES for k in ('initial_state', 'final_official_state')):
                    raise ValueError('M2目标和初次/最终官方状态无效')
                if not t.get('evidence_refs'):
                    raise ValueError('M2判定须有原文证据')
            if len(target_ids) != len(set(target_ids)):
                raise ValueError('M2目标ID重复')
        if m['id'] == 'M8' and obs is not None:
            if not isinstance(obs, dict) or 'retry_request_ids' not in obs or 'no_body_fetch_request_ids' not in obs:
                raise ValueError('M8须列重试和未取得正文请求ID，未知使用null')
            expected = cost_vector(rows, obs['retry_request_ids'], obs['no_body_fetch_request_ids'])
            actual = obs.get('C')
            if not isinstance(actual, dict) or set(actual) != set(expected) or any(actual[k] != v or (v is not None and type(actual[k]) is not int) for k, v in expected.items()):
                raise ValueError('M8成本向量与实际事件/所列ID不符')
            if (expected['R'] or expected['U']) and (not m.get('reason') or not m.get('evidence_refs')):
                raise ValueError('重试/未取得正文的归类须有理由和证据')
