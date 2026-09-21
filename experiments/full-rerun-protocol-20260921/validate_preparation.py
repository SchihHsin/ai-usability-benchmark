from pathlib import Path
import json,hashlib,subprocess,sys
import runner,assess
ROOT=Path(__file__).resolve().parent
p=json.loads((ROOT/'protocol.json').read_text()); tasks=json.loads((ROOT/'tasks.json').read_text())['tasks']
runner.verify_skill_manifest(ROOT/'frozen-skill')
jobs=[(t,e,m) for t in tasks for e in p['ecosystems'] for m in p['models']];assert len(jobs)==156
for t,e,m in jobs:
 assert runner.load_task({'tasks':tasks},t,e)
 assert tasks[t]['applicability'][e]
items=json.loads((ROOT/'validation-input/development.json').read_text());assert len(items)==18
assert all(i['prior'] for i in items)
for i in items:
 for kind in ['predictors','outcome']:
  prompt=assess.prompt(i,kind);assert 'applicability' in prompt
  assert i['question'] in json.loads(prompt.split('输入 JSON：\n',1)[1])['question']
  if kind=='predictors': assert 'final' not in json.loads(prompt.split('输入 JSON：\n',1)[1])
  # Verify original bytes, not just regenerated records.
  assert hashlib.sha256(((Path(i['run_dir']) if Path(i['run_dir']).is_absolute() else ROOT/Path(i['run_dir']))/'process.jsonl').read_bytes()).hexdigest()==i['metadata']['process_sha256']
result={'jobs_preflight':len(jobs),'existing_logs_parsed':len(items),'logs_with_prior':sum(bool(i['prior']) for i in items),'recovered_priors':[i['case'] for i in items if any(x.get('recovery') for x in i['prior'])],'old_logs_modified':False,'live_model_runs':0,'limits':'Structural regression and real-log parsing, not live assessor accuracy or completed full rerun.'}
(ROOT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
