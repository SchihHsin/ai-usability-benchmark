"""Append audited assessments to each run's existing evaluation.json; raw process stays immutable."""
from pathlib import Path
import argparse,copy,hashlib,json,sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'frozen-skill'))
from scripts import run_log,overall_score

def choose(case,kind,split):
    reviewed=ROOT/'reviewed'/split/f'{case}-{kind}.json'
    if reviewed.exists():return reviewed,json.loads(reviewed.read_text())
    for p in sorted((ROOT/'assessments'/split).glob(f'{case}-{kind}*.json'),key=lambda p:(p.stat().st_mtime_ns,p.name)):
        d=json.loads(p.read_text())
        ids=[x.get('id') for x in d.get('metrics' if kind=='predictors' else 'requirements',[])]
        if not d.get('error') and ids==([f'M{i}' for i in range(1,9)] if kind=='predictors' else list(range(1,7))):return p,d
    return None,None

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--split',required=True,choices=['development','heldout']);args=ap.parse_args()
    if args.split=='heldout' and not (ROOT/'frozen-selection.json').exists():raise ValueError('selection must be frozen')
    items=json.loads((ROOT/'assessment-input'/f'{args.split}.json').read_text());summary=[]
    for item in items:
        pp,p=choose(item['case'],'predictors',args.split);op,o=choose(item['case'],'outcome',args.split)
        if p is None or o is None:
            summary.append({'case':item['case'],'status':'assessment_missing'});continue
        dest=Path(item['run_dir']);events=run_log.events(dest);byid={x['id']:x for x in events};end=events[-1]
        hashes={str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in (pp,op)}
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
            if m.get('lower') is not None and m.get('upper') is not None and m['lower']<m['upper']:
                m['score']=None;m['status']='bounded'
            if m['id']=='M7' and not item['prior']:m.update(score=None,lower=1,upper=5,status='insufficient_evidence')
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
        overall=overall_score.calculate({m['id']:m for m in metrics})
        value={'rubric_version':events[0]['metadata']['rubric_version'],'assessor':{'id':'glm-5.3-with-deterministic-evidence-audit','method':'separate source/prior and outcome contexts; automatic assessment, not human gold'},'limitations':['No hardware execution. Literal evidence auditing cannot establish complete technical correctness.','M11 uses original baseline coefficients only; a fitted candidate is recorded at batch level, not silently adopted.'],'requirements':requirements,'metrics':metrics+[{'id':'M11',**overall}],'overall':overall,'evidence':evidence,'issues':[],'assessment_files':hashes,'m2_documents':p.get('m2_documents',[]),'quote_audit':p.get('quote_audit',[])+o.get('quote_audit',[])}
        run_log.save_evaluation(dest,value);check=run_log.check(dest)
        summary.append({'case':item['case'],'status':'saved','evidence_count':len(evidence),'check':check})
    (ROOT/f'{args.split}-consolidation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'split':args.split,'saved':sum(x['status']=='saved' for x in summary),'missing':sum(x['status']=='assessment_missing' for x in summary)},ensure_ascii=False))
if __name__=='__main__':main()
