"""Document-unit M2; semantic document identity must have review evidence."""
import copy
try:
    from . import body_state_metrics as body
except ImportError:
    import body_state_metrics as body
VERSION = 'v2-document-2026-09-15'

def adapted_rows(rows, documents):
    adapted=copy.deepcopy(rows)
    protocol=adapted[0]['metadata'].setdefault('protocol',{})
    protocol['acquisition_targets']=[dict(id=d['target_id'],description=d['description'],
        requirement_refs=d['requirement_refs']) for d in documents]
    return adapted

def template(rows):
    value=body.template(adapted_rows(rows,[]))
    value['rubric_version']=VERSION
    value['metrics'][1]['observation']['fetch_inventory']=[]
    return value

def aggregate(documents):
    ids=[d['target_id'] for d in documents]
    if len(ids)!=len(set(ids)): raise ValueError('同一文档不能重复进入M2分母')
    return body.aggregate(documents)

def validate(rows,value):
    m=value['metrics'][1];obs=m['observation'];docs=obs['targets']
    if obs['aggregate']!=aggregate(docs):raise ValueError('文档均值或去重不符')
    inventory=obs.get('fetch_inventory')
    if not isinstance(inventory,list):raise ValueError('须保留所有获取请求的归类')
    requests={r['id']:r for r in rows if r['type']=='tool_request' and r.get('role')=='fetch'}
    ids=[x.get('request_id') for x in inventory]
    if len(ids)!=len(set(ids)) or set(ids)-requests.keys():raise ValueError('获取归类重复或引用无效')
    results={r['request_id']:r for r in rows if r['type']=='tool_result'}
    docids={d['target_id'] for d in docs};assigned={x:[] for x in docids}
    urls=[u for d in docs for u in d.get('urls',[])]
    if len(urls)!=len(set(urls)):raise ValueError('同一正文URL不能在多个文档目标重复计分')
    evidence={e['id']:e for e in value['evidence']}
    for item in inventory:
        rid=item['request_id'];kind=item.get('source_class');doc=item.get('document_id')
        if kind not in {'official','third_party','unverified','not_dispatched'} or not item.get('reason'):
            raise ValueError('须说明来源归类及依据')
        if not item.get('event_refs'):raise ValueError('归类须引用获取事件')
        result=results.get(rid)
        if kind=='not_dispatched':
            if not result or result['tool_status']!='not_dispatched':raise ValueError('未派发须有真实拒绝事件')
        elif result and result['tool_status']=='not_dispatched':raise ValueError('未派发请求不能评为获取失败')
        if kind=='official':
            if doc not in docids:raise ValueError('官方获取请求须归入文档，不能删除失败项')
            assigned[doc].append(result['id'] if result else None)
        elif doc is not None:raise ValueError('非官方或未派发请求不进入官方M2')
    for d in docs:
        if not assigned[d['target_id']] or not d.get('identity_basis') or not d.get('urls'):
            raise ValueError('文档须有获取请求、URL和去重依据')
        if d.get('score') is not None and (None in assigned[d['target_id']] or not set(assigned[d['target_id']])<=set(d.get('event_refs',[]))):
            raise ValueError('文档评分须覆盖其全部获取返回，保留首次障碍')
        if d.get('score') is not None and any(evidence.get(e,{}).get('event_id') not in assigned[d['target_id']] for e in d.get('evidence_refs',[])):
            raise ValueError('文档获取评分不能引用第三方补足或其他文档替代本篇官方返回')
    if m.get('score') is not None:
        if set(ids)!=set(requests) or any(x['source_class']=='unverified' for x in inventory):
            raise ValueError('获取清单尚未完整归类，不得发布任务M2均值')
    body.validate(adapted_rows(rows,docs),value)
