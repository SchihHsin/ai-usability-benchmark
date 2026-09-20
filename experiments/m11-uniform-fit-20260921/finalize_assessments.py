"""Apply one final mechanical evidence-audit policy uniformly before fitting.
Original model judgments and failed attempts are never overwritten.
"""
from pathlib import Path
import argparse,copy,hashlib,json
import assess
ROOT=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--split',choices=['development','heldout'],required=True);a=ap.parse_args()
    if a.split=='heldout' and not (ROOT/'frozen-selection.json').exists():raise ValueError('freeze selection first')
    items=json.loads((ROOT/'assessment-input'/f'{a.split}.json').read_text());out=ROOT/'reviewed'/a.split;out.mkdir(parents=True,exist_ok=True);summary=[]
    for item in items:
        for kind in ('predictors','outcome'):
            paths=sorted((ROOT/'assessments'/a.split).glob(f"{item['case']}-{kind}*.json"),key=lambda p:(p.stat().st_mtime_ns,p.name))
            selected=None
            for p in paths:
                d=json.loads(p.read_text());ids=[x.get('id') for x in d.get('metrics' if kind=='predictors' else 'requirements',[])]
                if not d.get('error') and ids==([f'M{i}' for i in range(1,9)] if kind=='predictors' else list(range(1,7))):selected=(p,d);break
            if selected is None:summary.append({'case':item['case'],'kind':kind,'status':'missing'});continue
            p,d=selected;raw=copy.deepcopy(d.get('raw_assessment',d));v=assess.audit(raw,item,kind)
            if kind=='predictors':
                for m in v['metrics']:
                    if m.get('status')=='insufficient_evidence' and (m.get('lower') is None or m.get('upper') is None):m.update(score=None,lower=1,upper=5)
                    if m.get('lower') is not None and m.get('upper') is not None and m['lower']<m['upper']:m.update(score=None,status='bounded')
                    if m['id']=='M7' and not item['prior']:m.update(score=None,lower=1,upper=5,status='insufficient_evidence')
            v.update(case=item['case'],kind=kind,task_id=item['task_id'],ecosystem=item['ecosystem'],split=a.split,budget=item['budget'])
            v['_provenance']={'original_assessment':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'process_sha256':item['metadata']['process_sha256'],'policy':'literal-nonempty-quotes; final/run-end identify same input answer; controller M8; preserve declared intervals; applicable unknown uses full scale bounds; blocked/NA not imputed'}
            dest=out/f"{item['case']}-{kind}.json"
            if dest.exists() and json.loads(dest.read_text())!=v:raise ValueError(f'refuse to overwrite finalized assessment: {dest}')
            dest.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');summary.append({'case':item['case'],'kind':kind,'status':'finalized','path':str(dest.relative_to(ROOT))})
    (ROOT/f'{a.split}-finalization.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'split':a.split,'finalized':sum(x['status']=='finalized' for x in summary),'missing':sum(x['status']=='missing' for x in summary)}))
if __name__=='__main__':main()
