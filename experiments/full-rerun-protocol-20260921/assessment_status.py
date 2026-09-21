"""Report post-assessment phase completion without treating errors as scores."""
from pathlib import Path
from collections import Counter
import json, datetime
R=Path(__file__).resolve().parent

def phase_status(case,kind):
    files=sorted((R/'assessments/development').glob(case+'-'+kind+'*.json'))
    attempts=[]
    for path in files:
        v=json.loads(path.read_text())
        if not v.get('error'):
            return {'status':'completed','result':str(path.relative_to(R))}
        raw=v.get('raw_stdout',[]);raw=raw if isinstance(raw,list) else [raw]
        quota=any(isinstance(e,dict) and any(isinstance(x,dict) and (x.get('category')=='quota' or x.get('code')==14018) for x in e.get('errors_info',[])) for e in raw)
        attempts.append({'file':str(path.relative_to(R)),'quota':quota,'error':v.get('error')})
    n=sum(not a['quota'] for a in attempts)
    return {'status':'technical_attempts_exhausted' if n>=2 else 'pending','technical_attempts':n,'attempts':attempts}

def build():
    items=json.loads((R/'assessment-input/development.json').read_text())
    rows=[{'case':i['case'],'run_id':i['run_name'],'phases':{k:phase_status(i['case'],k) for k in ('predictors','outcome')}} for i in items]
    return {'updated':datetime.datetime.now().isoformat(timespec='seconds'),'summary':dict(Counter(p['status'] for r in rows for p in r['phases'].values())),'rows':rows,'note':'Phase completion means a saved schema-valid result, not semantic validation. Pending may be in-flight. Raw failures and recovered shapes remain saved. Default allowance is two nonquota technical attempts; see authorized-retry-20260921.json and authorized assessment records for the explicit additional allowance authorized by the user.'}
if __name__=='__main__':
    report=build();(R/'assessment-status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report['summary']))
