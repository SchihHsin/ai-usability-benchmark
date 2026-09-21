"""Append audited assessments to each run's existing evaluation.json; raw process stays immutable."""
from pathlib import Path
import argparse,copy,hashlib,json,sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'frozen-skill'))
from scripts import run_log,overall_score

def choose(case,kind,split,nreq):
    reviewed=ROOT/'reviewed'/split/f'{case}-{kind}.json'
    if reviewed.exists():return reviewed,json.loads(reviewed.read_text())
    for p in sorted((ROOT/'assessments'/split).glob(f'{case}-{kind}*.json'),key=lambda p:(p.stat().st_mtime_ns,p.name)):
        d=json.loads(p.read_text())
        ids=[x.get('id') for x in d.get('metrics' if kind=='predictors' else 'requirements',[])]
        if not d.get('error') and ids==([f'M{i}' for i in range(1,9)] if kind=='predictors' else list(range(1,nreq+1))):return p,d
    return None,None

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--split',required=True,choices=['development','heldout']);args=ap.parse_args()
    if args.split=='heldout' and not (ROOT/'frozen-selection.json').exists():raise ValueError('selection must be frozen')
    items=json.loads((ROOT/'assessment-input'/f'{args.split}.json').read_text());summary=[]
    for item in items:
        pp,p=choose(item['case'],'predictors',args.split,len(item['criteria']));op,o=choose(item['case'],'outcome',args.split,len(item['criteria']))
        if p is None or o is None:
            summary.append({'case':item['case'],'status':'assessment_missing'});continue
        dest=Path(item['run_dir']);events=run_log.events(dest);byid={x['id']:x for x in events};end=events[-1]
        hashes={str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in (pp,op)}
        hashes['consolidate_evaluations.py']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        channel_file=ROOT/'reviewed-channel-states.json'
        if channel_file.exists():hashes[str(channel_file.relative_to(ROOT))]=hashlib.sha256(channel_file.read_bytes()).hexdigest()
        saved=json.loads((dest/'evaluation.json').read_text())
        if any(x['evaluation'].get('assessment_files')==hashes for x in saved['revisions']):continue
        evidence=[]
        def add_ref(event_id,quote):
            if event_id in ('final','run-end'):event_id=end['id']
            row=byid.get(event_id)
            if not row or not isinstance(quote,str) or not quote:return None
            field=next((k for k in ('response','answer','content','question') if k in row and isinstance(row[k],dict) and 'content' in row[k]),None)
            if field is None:return None
            text=run_log.unpack(row[field]).decode('utf-8');pos=text.find(quote);encoded=False
            if pos<0 and field=='content':
                quote=json.dumps(quote,ensure_ascii=False)[1:-1];pos=text.find(quote);encoded=True
            if pos<0:return None
            eid='ev-'+str(len(evidence)+1)
            evidence.append({'id':eid,'event_id':event_id,'field':field,'sha256':row[field]['sha256'],'start':pos,'end':pos+len(quote),'quote':quote,'json_escaped':encoded})
            return eid
        metrics=[]
        for original in p['metrics']+o.get('m9_m10',[]):
            m=copy.deepcopy(original);refs=[]
            for ev in (m.get('evidence',[]) if isinstance(m.get('evidence',[]),list) else [m['evidence']]):
                r=add_ref(ev.get('event_id'),ev.get('quote'))
                if r:refs.append(r)
            m['evidence_refs']=refs;m['event_refs']=[]
            if m.get('status')=='bounded' and m.get('lower') is not None and m.get('upper') is not None and m['lower']<m['upper']:
                m['score']=None;m['status']='bounded'
            if m['id']=='M7' and not item['prior'] and not (ROOT/'prior-recovery'/(item['case']+'-input.json')).exists():m.update(score=None,lower=1,upper=5,status='insufficient_evidence')
            if m['id']=='M8':
                c=sum(item['counts'].values());sc=1 if c>=9 else 2 if c>=7 else 3 if c>=5 else 4 if c>=3 else 5 if c>=1 else None
                m.update(score=sc,lower=sc,upper=sc,status='scored' if sc else 'insufficient_evidence');m['event_refs']=[x['id'] for x in events if x['type']=='tool_dispatch']
            metrics.append(m)
        for mid in ('M9','M10'):
            if not any(m['id']==mid for m in metrics):metrics.append({'id':mid,'score':None,'status':'not_assessed','reason':'Assessor did not return this metric','evidence_refs':[],'event_refs':[]})
        requirements=[]
        for original in o['requirements']:
            r=copy.deepcopy(original);r['evidence_refs']=[]
            for eid,q in ((end['id'],r.get('answer_quote')),(r.get('evidence_id'),r.get('evidence_quote'))):
                ref=add_ref(eid,q)
                if ref:r['evidence_refs'].append(ref)
            requirements.append(r)
        issues=[]
        documents=p.get('m2_documents',[])
        for doc in documents:
            if doc.get('representation') not in ('none','frame'):continue
            first_id=doc.get('event_id');first_seq=byid.get(first_id,{}).get('seq',0)
            alternatives=[d.get('event_id') for d in documents if d.get('representation')=='body' and byid.get(d.get('event_id'),{}).get('seq',0)>first_seq]
            issues.append({'id':'fetch-'+str(first_id),'type':'target_body_not_obtained','initial_obstacle_event_id':first_id,'alternative_body_event_ids':alternatives,'recovery_status':'other_body_obtained_later' if alternatives else 'no_later_body_observed','task_resolution':'not_inferred_from_fetch_state'})
        channel_states={}
        mm={m['id']:m for m in metrics}
        official=[d for d in documents if d.get('ownership')=='official']
        if official and all(d.get('representation') in ('none','frame') for d in official) and mm['M3'].get('status')=='blocked' and not any(x.startswith('M2:') for x in p.get('execution_gate',{}).get('errors',[])):
            channel_states['official']={'status':'confirmed_unavailable','reason':'完整获取清单中官方返回均无正文，M3已评为受阻；只限本轮取得支撑','evidence':[d['event_id'] for d in official]}
        channel_file=ROOT/'reviewed-channel-states.json'
        manual=json.loads(channel_file.read_text()).get(item['case']) if channel_file.exists() else None
        if manual:
            if manual['process_sha256']!=hashlib.sha256((dest/'process.jsonl').read_bytes()).hexdigest():raise ValueError('channel review process hash mismatch')
            for name,state in manual['channels'].items():
                if not state.get('reason') or not state.get('evidence') or any(e not in byid for e in state['evidence']):raise ValueError('channel review evidence mismatch')
                channel_states[name]=state
        overall=overall_score.calculate({m['id']:m for m in metrics},channel_states)
        value={'rubric_version':events[0]['metadata']['rubric_version'],'assessor':{'id':'glm-5.3-with-recorded-evidence-review','method':'separate source/prior and outcome contexts; automatic assessment with recorded Luna/root review corrections, not human gold'},'limitations':['No hardware execution. Literal evidence auditing cannot establish complete technical correctness.','M11 uses original baseline coefficients only; this full run does not fit or adopt replacement coefficients.'],'requirements':requirements,'metrics':metrics+[{'id':'M11',**overall}],'overall':overall,'channel_states':channel_states,'execution_gate':{'predictors':p.get('execution_gate'),'outcome':o.get('execution_gate')},'evidence':evidence,'issues':issues,'assessment_files':hashes,'m2_documents':p.get('m2_documents',[]),'quote_audit':[q for q in p.get('quote_audit',[])+o.get('quote_audit',[]) if q.get('metric')!='M8'],'superseded_m8_quote_audit':[q for q in p.get('quote_audit',[])+o.get('quote_audit',[]) if q.get('metric')=='M8'],'m8_audit_basis':'M8 recomputed from actual dispatch events above; assessor count quotations are retained separately and do not override recorded counts'}
        run_log.save_evaluation(dest,value);check=run_log.check(dest)
        summary.append({'case':item['case'],'status':'saved','evidence_count':len(evidence),'check':check})
    (ROOT/f'{args.split}-consolidation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'split':args.split,'saved':sum(x['status']=='saved' for x in summary),'missing':sum(x['status']=='assessment_missing' for x in summary)},ensure_ascii=False))
if __name__=='__main__':main()
