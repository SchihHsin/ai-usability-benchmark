"""Resume remaining GLM runs after an exhausted technical cell; leaves frozen runner untouched."""
from pathlib import Path
from types import SimpleNamespace
import json,sys,hashlib
import runner
from completion_guard import errors as completion_errors, invalid_ids
R=Path(__file__).resolve().parent
MODEL='glm-5.3'
EXHAUSTED={('U','cuda'): {'reason':'two technical failures exhausted retry allowance','runs':['U-cuda-glm-5_3-standard-20260921T133705','U-cuda-glm-5_3-standard-20260921T134726']}}
def main():
 p=json.loads((R/'protocol.json').read_text()); assert MODEL in p['models']
 freeze=json.loads((R/'freeze-manifest.json').read_text())
 for name,digest in freeze.items():
  assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest, name+' changed after freeze'
 ledger=R/('ledger-'+MODEL+'.jsonl'); done={}
 exfile=R/'collection-exhausted.json'
 if exfile.exists():
  for z in json.loads(exfile.read_text()).get('skipped',[]):
   EXHAUSTED[(z['task'],z['ecosystem'])]={'reason':z.get('reason','two technical failures exhausted retry allowance'),'runs':z.get('runs',[])}
 if ledger.exists():
  for line in ledger.read_text().splitlines():
   x=json.loads(line)
   if x.get('completed') and x['run_id'] not in invalid_ids(): done[(x['task'],x['ecosystem'])]=x
 skipped=[]
 for k,v in EXHAUSTED.items():
  skipped.append({'task':k[0],'ecosystem':k[1],**v})
 (R/'collection-exhausted.json').write_text(json.dumps({'model':MODEL,'skipped':skipped},ensure_ascii=False,indent=2)+'\n')
 args=SimpleNamespace(root=R,protocol=R/'protocol.json',tasks=R/'tasks.json',skill=R/'frozen-skill',search_budget=None,fetch_budget=None,repetition=1)
 fail_counts={}
 if ledger.exists():
  for line in ledger.read_text().splitlines():
   x=json.loads(line)
   if not x.get('completed') and x.get('task') and x.get('ecosystem'):
    fail_counts[(x['task'],x['ecosystem'])]=fail_counts.get((x['task'],x['ecosystem']),0)+1
 for n,t in enumerate(p['development']):
  ecos=p['ecosystems'] if n%2==0 else list(reversed(p['ecosystems']))
  for e in ecos:
   if (t,e) in done or (t,e) in EXHAUSTED: continue
   while True:
    rid=runner.one_run(args,t,e,'standard',MODEL)
    ev=json.loads((R/'runs'/rid/'evaluation.json').read_text()); ex=ev['revisions'][-1]['evaluation'].get('execution',{})
    check=json.loads((R/(rid+'-check.json')).read_text())
    completed=ex.get('exit_code')==0 and not ex.get('adapter_errors') and ex.get('stop_reason')=='client_complete' and not check.get('issues') and bool(ex.get('models')) and not completion_errors(R/'runs'/rid)
    rec={'completion_errors':completion_errors(R/'runs'/rid),'completed':completed,'stop_reason':ex.get('stop_reason'),'check_issues':check.get('issues'),'task':t,'ecosystem':e,'model':MODEL,'run_id':rid,'exit_code':ex.get('exit_code'),'response_models':ex.get('models'),'adapter_errors':ex.get('adapter_errors')}
    with ledger.open('a') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    if completed:
     done[(t,e)]=rec; break
    fail_counts[(t,e)]=fail_counts.get((t,e),0)+1
    if fail_counts[(t,e)]>=2:
     EXHAUSTED[(t,e)]={'reason':'two technical failures exhausted retry allowance','runs':[json.loads(line).get('run_id') for line in ledger.read_text().splitlines() if json.loads(line).get('task')==t and json.loads(line).get('ecosystem')==e and not json.loads(line).get('completed')]}
     skipped.append({'task':t,'ecosystem':e,**EXHAUSTED[(t,e)]})
     (R/'collection-exhausted.json').write_text(json.dumps({'model':MODEL,'skipped':skipped},ensure_ascii=False,indent=2)+'\n')
     break
    # first technical failure: one immediate retry under standing authorization
if __name__=='__main__': main()
