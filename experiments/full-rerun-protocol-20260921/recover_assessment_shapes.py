"""Recover unambiguous JSON container errors, preserving every original judgment."""
from pathlib import Path
import json,copy
import assess
from review_gate import check
R=Path(__file__).resolve().parent
items={i['case']:i for i in json.loads((R/'assessment-input/development.json').read_text())}
for f in (R/'assessments/development').glob('*.json'):
 d=json.loads(f.read_text());case=d.get('case');kind=d.get('kind')
 if case not in items or 'exact schema mismatch' not in d.get('error',''):continue
 good=[g for g in f.parent.glob(case+'-'+kind+'*.json') if not json.loads(g.read_text()).get('error')]
 if good:continue
 v,_,_=assess.extract(d['raw_stdout']);v=copy.deepcopy(v);repair=None
 if kind=='predictors':
  wanted=[f'M{i}' for i in range(1,9)];kept=[m for m in v.get('metrics',[]) if m.get('id') in wanted];extra=[m for m in v.get('metrics',[]) if m.get('id') not in wanted]
  if [m['id'] for m in kept]==wanted and extra and all(str(m.get('id','')).endswith(('-note', '_note')) and all(m.get(k) is None for k in ('score','lower','upper')) for m in extra):
   v['metrics']=kept;v['supplementary_notes']=extra;repair='Move non-metric note entries to supplementary_notes; keep all eight grades unchanged.'
 elif kind=='outcome' and 'm9_m10' not in v:
  req=v.get('requirements',[]);notes=[m for m in req if m.get('id') in ('M9','M10')];requirements=[m for m in req if isinstance(m.get('id'),int)]
  if [m['id'] for m in notes]==['M9','M10'] and [m['id'] for m in requirements]==list(range(1,len(items[case]['criteria'])+1)) and len(req)==len(notes)+len(requirements):
   v['m9_m10']=notes;v['requirements']=requirements;repair='Move M9/M10 objects from requirements into their schema field; preserve all values.'
 if not repair:continue
 raw=copy.deepcopy(v);assess.check=check;v=assess.audit(v,items[case],kind)
 v.update({k:d[k] for k in ['case','task_id','ecosystem','split','kind','_audit'] if k in d});v['raw_assessment']=raw;v['shape_recovery']={'source':str(f.relative_to(R)),'action':repair,'new_model_call':False}
 dest=f.parent/(case+'-'+kind+'-shape-recovered.json');dest.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');print(dest.name)
