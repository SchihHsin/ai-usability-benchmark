"""One model's 52 runs, resumable from a controller ledger. No score-based retries."""
from pathlib import Path
from types import SimpleNamespace
import json,sys,hashlib
import runner
from completion_guard import errors as completion_errors,invalid_ids
R=Path(__file__).resolve().parent

def main():
 model=sys.argv[1];p=json.loads((R/'protocol.json').read_text());assert model in p['models']
 freeze=json.loads((R/'freeze-manifest.json').read_text())
 for name,digest in freeze.items():
  assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest, name+' changed after freeze'
 ledger=R/('ledger-'+model+'.jsonl');done={}
 if ledger.exists():
  for line in ledger.read_text().splitlines():
   x=json.loads(line);
   if x.get('completed') and x['run_id'] not in invalid_ids():done[(x['task'],x['ecosystem'])]=x
 args=SimpleNamespace(root=R,protocol=R/'protocol.json',tasks=R/'tasks.json',skill=R/'frozen-skill',search_budget=None,fetch_budget=None,repetition=1)
 for n,t in enumerate(p['development']):
  ecos=p['ecosystems'] if n%2==0 else list(reversed(p['ecosystems']))
  for e in ecos:
   if (t,e) in done:continue
   rid=runner.one_run(args,t,e,'standard',model)
   ev=json.loads((R/'runs'/rid/'evaluation.json').read_text());ex=ev['revisions'][-1]['evaluation'].get('execution',{})
   check=json.loads((R/(rid+'-check.json')).read_text())
   completed=ex.get('exit_code')==0 and not ex.get('adapter_errors') and ex.get('stop_reason')=='client_complete' and not check.get('issues') and bool(ex.get('models')) and not completion_errors(R/'runs'/rid)
   record={'completion_errors':completion_errors(R/'runs'/rid),'completed':completed,'stop_reason':ex.get('stop_reason'),'check_issues':check.get('issues'),'task':t,'ecosystem':e,'model':model,'run_id':rid,'exit_code':ex.get('exit_code'),'response_models':ex.get('models'),'adapter_errors':ex.get('adapter_errors')}
   with ledger.open('a') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
   if not completed:
    raise SystemExit('Technical run issue saved; review before resuming: '+rid)
if __name__=='__main__':main()
