from completion_guard import invalid_ids
"""Audit every selected logical unit against frozen resources and raw run log."""
from pathlib import Path
import hashlib,json,sys,datetime
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'frozen-skill'))
from scripts import run_log
p=json.loads((R/'protocol.json').read_text());freeze=json.loads((R/'freeze-manifest.json').read_text());issues=[];runs=[];missing=[]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
for path,h in freeze.items():
 if sha(R/path)!=h:issues.append({'kind':'frozen_hash_mismatch','file':path})
for model in p['models']:
 ledger=[json.loads(l) for l in (R/f'ledger-{model}.jsonl').read_text().splitlines()];selected={}
 for x in ledger:
  if x.get('completed') and x['run_id'] not in invalid_ids():selected[(x['task'],x['ecosystem'])]=x
 for task in p['development']:
  for eco in p['ecosystems']:
   if (task,eco) not in selected:missing.append([model,task,eco]);continue
   x=selected[(task,eco)];r=R/'runs'/x['run_id'];events=run_log.events(r);meta=events[0]['metadata'];errors=[]
   for field,name in [('protocol_sha256','protocol.json'),('tasks_sha256','tasks.json')]:
    if meta.get(field)!=sha(R/name):errors.append(field)
   for path,h in meta.get('skill_hashes',{}).items():
    if sha(R/'frozen-skill'/path)!=h:errors.append('skill:'+path)
   check=run_log.check(r);errors.extend(check['issues'])
   versions=json.loads((r/'evaluation.json').read_text())['revisions'];execution=next((v['evaluation']['execution'] for v in versions if 'execution' in v['evaluation']),{})
   if execution.get('exit_code')!=0 or execution.get('stop_reason')!='client_complete' or execution.get('adapter_errors'):errors.append('execution_not_complete')
   if execution.get('model_requested')!=model or model not in execution.get('models',[]):errors.append('model_identity')
   if events[-1].get('type')!='run_end':errors.append('no_run_end')
   assessment=next((v['evaluation'] for v in reversed(versions) if v['evaluation'].get('assessment_files')),None)
   if assessment:
    ids=[m['id'] for m in assessment['metrics']]
    if ids!=[f'M{i}' for i in range(1,12)]:errors.append('metric_inventory')
   runs.append({'run_id':r.name,'process_sha256':sha(r/'process.jsonl'),'errors':errors,'assessed':bool(assessment),'m11_status':(assessment or {}).get('overall',{}).get('status'),'dispatch_counts':check.get('counts',{}).get('dispatched')})
   issues.extend({'run_id':r.name,'kind':e} for e in errors)
out={'updated':datetime.datetime.now().isoformat(timespec='seconds'),'expected':156,'selected':len(runs),'missing_jobs':missing,'issues':issues,'runs':runs,'collection_complete':len(runs)==156 and not issues,'assessment_complete':len(runs)==156 and all(x['assessed'] for x in runs),'note':'Automated integrity and protocol checks only; does not certify semantic scoring or task execution on hardware.'}
(R/'batch-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['missing_jobs','runs','note']},ensure_ascii=False))
