"""Post-assess one model's completed runs; retain technical retries separately."""
from pathlib import Path
from types import SimpleNamespace
import json,sys
import prepare_assessment,assess
R=Path(__file__).resolve().parent
if __name__=='__main__':
 model=sys.argv[1];p=json.loads((R/'protocol.json').read_text());tasks=json.loads((R/'tasks.json').read_text())['tasks'];args=SimpleNamespace(timeout=300,overwrite=False)
 ledger=[json.loads(x) for x in (R/('ledger-'+model+'.jsonl')).read_text().splitlines()];runs={ (x['task'],x['ecosystem']):x for x in ledger if x.get('completed')}
 for r in runs.values():
  item=prepare_assessment.parse_run((R/'runs'/r['run_id']/'process.jsonl').resolve(),tasks,p)
  for kind in ['predictors','outcome']:
   status=assess.run_one(item,kind,args);print(json.dumps(status),flush=True)
