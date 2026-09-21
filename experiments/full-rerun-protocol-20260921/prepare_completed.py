from completion_guard import invalid_ids
"""Prepare assessments only for controller-verified successful logical units."""
from pathlib import Path
import json,hashlib
import prepare_assessment
R=Path(__file__).resolve().parent
p=json.loads((R/'protocol.json').read_text());tasks=json.loads((R/'tasks.json').read_text())['tasks'];items=[];attempts=[]
for model in p['models']:
 ledger=R/('ledger-'+model+'.jsonl');selected={}
 if not ledger.exists():continue
 for line in ledger.read_text().splitlines():
  row=json.loads(line);attempts.append(row)
  if row.get('completed') and row['run_id'] not in invalid_ids():selected[(row['task'],row['ecosystem'])]=row
 for r in selected.values():
  item=prepare_assessment.parse_run((R/'runs'/r['run_id']/'process.jsonl').resolve(),tasks,p)
  items.append(item)
out=R/'assessment-input';out.mkdir(exist_ok=True);(out/'development.json').write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n')
(R/'assessment-selection.json').write_text(json.dumps({'selected':len(items),'expected':156,'rule':'completed ledger units only; technical attempts retained but not scored as model answers','attempts':attempts,'process_hashes':{i['case']:i['metadata']['process_sha256'] for i in items}},ensure_ascii=False,indent=2)+'\n');print(json.dumps({'selected':len(items),'expected':156}))
