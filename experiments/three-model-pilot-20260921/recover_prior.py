"""Repair a missing closing tag using pre-tool event boundaries; re-assess M7 only."""
from pathlib import Path
from types import SimpleNamespace
import json,copy
import assess
from prepare_assessment import unpack,visible_text
R=Path(__file__).resolve().parent
items=json.loads((R/'assessment-input/development.json').read_text());repairs=[]
for item in items:
 if item['prior']:continue
 rows=[json.loads(x) for x in (Path(item['run_dir'])/'process.jsonl').read_text().splitlines()];prior=[]
 for e in rows:
  if e['type']=='tool_request':break
  if e['type']!='client_note':continue
  try:o=json.loads(unpack(e['content']))
  except Exception:continue
  if o.get('type')!='assistant':continue
  t='\n'.join(visible_text(o.get('message',o).get('content',[])))
  if '<prior_answer>' in t and '</prior_answer>' not in t:
   prior.append({'event_id':e['id'],'text':t.split('<prior_answer>',1)[1].strip()})
 if not prior:continue
 repaired=copy.deepcopy(item);repaired['prior']=prior
 repairs.append({'case':item['case'],'reason':'unclosed prior tag; entire recovered visible text precedes first tool request','prior':prior,'original_process_unchanged':True})
 rr=R/'prior-recovery';rr.mkdir(exist_ok=True);(rr/(item['case']+'-input.json')).write_text(json.dumps(repaired,ensure_ascii=False,indent=2)+'\n')
 assess.ROOT=rr
 print(assess.run_one(repaired,'predictors',SimpleNamespace(overwrite=False,timeout=300)),flush=True)
(R/'prior-recovery.json').write_text(json.dumps(repairs,ensure_ascii=False,indent=2)+'\n')
