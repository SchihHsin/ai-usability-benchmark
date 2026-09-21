"""Deterministic evidence/aggregation checks; does not establish semantic truth."""
from urllib.parse import urldefrag

def check(value,item,kind):
    errors=[]; sources={x['event_id']:x for x in item['sources']}
    def cited(evidence,final=False):
        if not isinstance(evidence,list) or any(not isinstance(e,dict) for e in evidence): return False
        return bool(evidence) and all(isinstance(e.get('quote'),str) and e['quote'].strip() and ((e.get('event_id')=='run-end' and e['quote'] in item['final']) if final else (e.get('event_id') in sources and e['quote'] in sources[e['event_id']]['text'])) for e in evidence)
    metrics=value.get('metrics',[]) if kind=='predictors' else value.get('m9_m10',[])
    byid={m['id']:m for m in metrics}
    for m in metrics:
        score=m.get('score')
        if score is not None and m.get('id')!='M2' and (isinstance(score,bool) or not isinstance(score,(int,float)) or score not in (1,2,3,4,5)):errors.append(m['id']+': invalid ordinal grade')
    for key in ('M4','M9','M10'):
        if key not in byid:continue
        scope=item['applicability'][key];m=byid[key]
        if not scope['applicable']:m.update(score=None,lower=None,upper=None,status='not_applicable',reason=scope['scope'])
        elif m.get('status')=='not_applicable':errors.append(key+': contradicts predefined applicability')
    if kind=='outcome':
        for m in metrics:
            if m.get('score') is not None and not cited(m.get('evidence',[]),True):errors.append(m['id']+': missing/invalid final answer citation')
    else:
        # Every dispatched fetch in the source input must be classified, including failed/unknown sources.
        fetch=[s for s in item['sources'] if s.get('role')=='fetch']; entries=value.get('m2_documents',[])
        ids=[x.get('event_id') for x in entries]
        if len(ids)!=len(set(ids)) or set(ids)!={s['event_id'] for s in fetch}:errors.append('M2: incomplete/duplicate fetch inventory')
        latest={}
        for s in fetch:latest[item.get('reviewed_document_groups',{}).get(s['event_id'],urldefrag(s.get('url') or s['event_id'])[0])]=s['event_id']
        bounds=[]; byevent={x.get('event_id'):x for x in entries}
        for eid in latest.values():
            d=byevent.get(eid,{})
            if d.get('ownership')=='third_party':continue
            if d.get('ownership')!='official':errors.append('M2: ownership unknown '+eid);continue
            state=d.get('representation'); ev=d.get('evidence',[])
            if not cited(ev) or not any(x.get('event_id')==eid for x in ev):errors.append('M2: missing return evidence '+eid)
            if state in ('none','frame','summary'):b={'none':(1,1),'frame':(2,2),'summary':(3,3)}[state]
            elif state=='body':
                c=d.get('completeness','unknown');b=(4,5)
                if c=='complete':
                    # Reference evidence is separate from model-visible sources, auditable by caller.
                    ref=d.get('reference',{});ref=ref if isinstance(ref,dict) else {};refid=ref.get('id');refs=item.get('completeness_references',{})
                    if refid not in refs or not refs[refid].get('verified_complete') or refs[refid].get('event_id')!=eid:errors.append('M2: unverified complete-body reference '+eid)
                    else:b=(5,5)
                elif c=='incomplete':
                    if not cited(d.get('boundary_evidence',[])):errors.append('M2: incomplete boundary evidence '+eid)
                    else:b=(4,4)
            else:b=(1,5)
            bounds.append(b)
        if not any(x.startswith('M2:') for x in errors) and bounds:
            lo=sum(x[0] for x in bounds)/len(bounds);hi=sum(x[1] for x in bounds)/len(bounds)
            byid['M2'].update(score=lo if lo==hi else None,lower=lo,upper=hi,status='scored' if lo==hi else 'bounded',reason='程序按独立文档最终获取状态等权聚合；未知项保留')
        elif not bounds:errors.append('M2: no assessable official document')
        m=byid.get('M4',{});score=m.get('score');c=value.get('m4_check',{})
        if score is not None:
            official_ids={d.get('event_id') for d in entries if d.get('ownership')=='official'}
            if not cited(c.get('evidence',[])) or any(ev.get('event_id') not in official_ids and not any(ev.get('event_id')==r.get('event_id') and ev.get('quote')==r.get('quote') for r in item.get('reviewed_official_search_evidence',[])) for ev in c.get('evidence',[])):errors.append('M4: missing official constraint citations')
            if not c.get('required_relations'):errors.append('M4: missing required relations')
            if score>=3 and c.get('unresolved_conflicts'):errors.append('M4: unresolved conflict cannot score >=3')
            if score>=4 and c.get('missing_relations'):errors.append('M4: missing relation cannot score >=4')
            if score==4 and (c.get('determination')!='combined' or not c.get('combination')):errors.append('M4: grade4 needs explicit constraint combination')
            if score==5 and c.get('determination')!='direct':errors.append('M4: grade5 needs direct applicability rule')
    # Reject only affected point values; keep raw assessment in caller, do not erase evidence.
    for m in metrics:
        own=[x for x in errors if x.startswith(m['id']+':')]
        if own:m.update(score=None,lower=None,upper=None,status='insufficient_evidence',reason='; '.join(own))
    value['execution_gate']={'errors':errors,'passed':not errors,'scope':'structural evidence checks, not semantic validation'}
    return value
