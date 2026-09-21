from completion_guard import invalid_ids
"""Post-assess one model's completed runs; retain technical retries separately."""
from pathlib import Path
from types import SimpleNamespace
import json,sys,fcntl
import prepare_assessment,assess
from review_gate import check
assess.check=check
R=Path(__file__).resolve().parent
original_prompt=assess.prompt
def exact_prompt(item,kind):
 text=original_prompt(item,kind)
 if kind=='outcome':
  schema=assess.output_schema(kind);fixed=json.loads(json.dumps(schema));n=len(item['criteria']);fixed['properties']['requirements']['minItems']=n;fixed['properties']['requirements']['maxItems']=n;fixed['properties']['requirements']['items']['properties']['id']['maximum']=n
  text=text.replace(json.dumps(schema,ensure_ascii=False),json.dumps(fixed,ensure_ascii=False))
  text+='\nrequirements必须严格对应输入criteria的'+str(n)+'项，ID='+str(list(range(1,n+1)))+'；原题内部子要求在该项reason内逐项解释，不另造顶层ID。'
 return text
assess.prompt=exact_prompt
if __name__=='__main__':
 model=sys.argv[1];p=json.loads((R/'protocol.json').read_text());tasks=json.loads((R/'tasks.json').read_text())['tasks'];args=SimpleNamespace(timeout=900,overwrite=False)
 ledger=[json.loads(x) for x in (R/('ledger-'+model+'.jsonl')).read_text().splitlines()];runs={ (x['task'],x['ecosystem']):x for x in ledger if x.get('completed') and x['run_id'] not in invalid_ids()}
 for r in runs.values():
  item=prepare_assessment.parse_run((R/'runs'/r['run_id']/'process.jsonl').resolve(),tasks,p)
  for source in item['sources']:
   if source.get('status')=='not_dispatched':source['role']='blocked_request'
  for kind in ['predictors','outcome']:
   locks=R/'.assessment-locks';locks.mkdir(exist_ok=True)
   with (locks/(item['case']+'-'+kind)).open('w') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    existing=list((R/'assessments/development').glob(item['case']+'-'+kind+'*.json'))
    good=[f for f in existing if not json.loads(f.read_text()).get('error')]
    if good:continue
    nonquota=[]
    for attempt in existing:
     record=json.loads(attempt.read_text());raw=record.get('raw_stdout',[]);raw=raw if isinstance(raw,list) else [raw]
     quota=any(isinstance(e,dict) and any(info.get('category')=='quota' or info.get('code')==14018 for info in e.get('errors_info',[]) if isinstance(info,dict)) for e in raw)
     if not quota:nonquota.append(attempt)
    if len(nonquota)>=2:
     print(json.dumps({'case':item['case'],'kind':kind,'status':'needs_review_after_two_technical_attempts'}),flush=True);continue
    args.overwrite=bool(existing)
    status=assess.run_one(item,kind,args);print(json.dumps(status),flush=True)
