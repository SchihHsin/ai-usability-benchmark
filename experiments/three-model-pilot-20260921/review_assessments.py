"""Mechanical post-run audit. Preserve raw scores; do not re-prompt for better scores."""
from pathlib import Path
import json,copy,hashlib
import assess
R=Path(__file__).resolve().parent
items=json.loads((R/'assessment-input/development.json').read_text());out=R/'reviewed/development';out.mkdir(parents=True,exist_ok=True);log=[]
m2_by_run={x['run_id']:x for x in json.loads((R/'m2-document-audit.json').read_text())}
m4_decisions={x['case']:x for x in json.loads((R/'m4-adjudication.json').read_text())['decisions']}
allowed={'scored','bounded','not_applicable','insufficient_evidence','blocked'}
for item in items:
 for kind in ('predictors','outcome'):
  paths=sorted((R/'assessments/development').glob(item['case']+'-'+kind+'*.json'),key=lambda p:(p.stat().st_mtime_ns,p.name));chosen=None
  for p in paths:
   d=json.loads(p.read_text())
   if not d.get('error') and d.get('raw_assessment'):chosen=(p,d);break
  if not chosen:continue
  p,d=chosen;raw=copy.deepcopy(d['raw_assessment']);changes=[]
  # Correct only a provable final-text location; never repair paraphrased quotations.
  if kind=='outcome':
   for q in raw.get('requirements',[]):
    if q.get('answer_quote') and q['answer_quote'] in item['final'] and q.get('answer_event_id') not in ('run-end','final'):
     changes.append({'field':'answer_event_id','id':q['id'],'before':q.get('answer_event_id'),'after':'run-end','basis':'literal quote in retained final output'});q['raw_answer_event_id']=q.get('answer_event_id');q['answer_event_id']='run-end'
   for m in raw.get('m9_m10',[]):
    for e in m.get('evidence',[]):
     if e.get('quote') and e['quote'] in item['final'] and e.get('event_id') not in ('run-end','final'):
      changes.append({'field':'metric_final_event_id','id':m['id'],'before':e.get('event_id'),'after':'run-end','basis':'literal quote in retained final output'});e['raw_event_id']=e.get('event_id');e['event_id']='run-end'
  for m in raw.get('metrics',[])+raw.get('m9_m10',[]):
   if m.get('score') is not None and m.get('status') not in allowed:
    changes.append({'field':'status','id':m['id'],'before':m.get('status'),'after':'scored','basis':'numeric judgment; evidence audited separately'});m['raw_status_label']=m.get('status');m['status']='scored'
  recovered_item_path=R/'prior-recovery'/(item['case']+'-input.json')
  if kind=='predictors' and recovered_item_path.exists():
   recovered_output=R/'prior-recovery/assessments/development'/(item['case']+'-predictors.json')
   if recovered_output.exists():
    recovered=json.loads(recovered_output.read_text())
    if not recovered.get('error'):
     item=json.loads(recovered_item_path.read_text())
     replacement=next(x for x in recovered['raw_assessment']['metrics'] if x['id']=='M7')
     raw['metrics']=[copy.deepcopy(replacement) if m['id']=='M7' else m for m in raw['metrics']]
     changes.append({'field':'M7','basis':'recovered unclosed pre-tool prior; targeted post-evaluation repair','source':str(recovered_output.relative_to(R))})
  val=assess.audit(raw,item,kind)
  for m in val.get('metrics',[])+val.get('m9_m10',[]):
   if m.get('lower') is not None and m.get('upper') is not None and m['lower']<m['upper']:m['score']=None;m['status']='bounded'
   if m['id'] in ('M9','M10') and m.get('score') is not None and not m.get('evidence'):
    m.update(score=None,status='insufficient_evidence',reason='最终回答评分未给出可核对原文引用；原评分保留在原始后评文件')
   if m['id']=='M7' and not item['prior']:m.update(score=None,status='insufficient_evidence',reason='未保存检索前回答')
   if m['id']=='M4' and item['case'] in m4_decisions:
    m['raw_model_score']=m.get('score');m['raw_model_status']=m.get('status');m.update({k:v for k,v in m4_decisions[item['case']].items() if k not in ('case','metric')})
   if m['id']=='M2':
    document_review=m2_by_run[item['run_name']]
    m['raw_model_score']=m.get('score');m['raw_model_status']=m.get('status')
    m.update(document_review['aggregate']);m['evidence']=[ev for doc in document_review['documents'] for ev in doc['evidence']]
    val['raw_model_m2_documents']=val.get('m2_documents',[]);val['m2_documents']=document_review['documents']
  val.update(case=item['case'],task_id=item['task_id'],ecosystem=item['ecosystem'],kind=kind,split='development',budget=item['budget'])
  val['_provenance']={'original_assessment':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'process_sha256':item['metadata']['process_sha256'],'changes':changes,'policy':'post-run deterministic event-ID/status repair; exact quotes only; M2 independently reviewed per document and aggregated with all unknown intervals included; not a new scoring rubric'}
  (out/(item['case']+'-'+kind+'.json')).write_text(json.dumps(val,ensure_ascii=False,indent=2)+'\n');log.append({'case':item['case'],'kind':kind,'changes':changes,'remaining_quote_issues':val.get('quote_audit',[])})
(R/'review-audit.json').write_text(json.dumps(log,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'reviewed':len(log),'mechanical_repairs':sum(len(x['changes']) for x in log)}))
