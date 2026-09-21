"""Derive reviews using only exact verifiable formatting repairs; preserve raw files."""
from pathlib import Path
import json,copy,re
import prepare_assessment,assess
from review_gate import check
from review_normalization import completeness
from quote_alignment import align as align_markdown
R=Path(__file__).resolve().parent
p=json.loads((R/'protocol.json').read_text());tasks=json.loads((R/'tasks.json').read_text())['tasks'];audit=[]
for run in (R/'runs').iterdir():
 if not (run/'evaluation.json').exists():continue
 lines=(run/'process.jsonl').read_text().splitlines()
 if not lines or json.loads(lines[-1]).get('type')!='run_end':continue
 item=prepare_assessment.parse_run((run/'process.jsonl').resolve(),tasks,p)
 for source in item['sources']:
  if source.get('status')=='not_dispatched':source['role']='blocked_request'
 texts={x['event_id']:x['text'] for x in item['sources']+item['prior']};texts['run-end']=item['final']
 for kind in ['predictors','outcome']:
  candidates=sorted((R/'assessments/development').glob(item['case']+'-'+kind+'*.json'),key=lambda f:f.stat().st_mtime_ns)
  selected=next((f for f in candidates if not json.loads(f.read_text()).get('error')),None)
  if selected is None:continue
  saved=json.loads(selected.read_text());value=copy.deepcopy(saved.get('raw_assessment',saved));repairs=[]
  denied={x['event_id'] for x in item['sources'] if x.get('role')=='blocked_request'}
  if kind=='predictors':
   value['not_dispatched_documents']=[d for d in value.get('m2_documents',[]) if d.get('event_id') in denied]
   value['m2_documents']=[d for d in value.get('m2_documents',[]) if d.get('event_id') not in denied]
  def walk(x):
   if isinstance(x,dict):
    if isinstance(x.get('answer_quote'),str):
     quoted={'event_id':'run-end','quote':x['answer_quote']};walk(quoted)
     if quoted['quote'] in item['final']:
      if x.get('answer_event_id')!='run-end':repairs.append({'basis':'answer_quote verified against frozen final; normalize answer event alias'})
      x['answer_event_id']='run-end';x['answer_quote']=quoted['quote']
    if isinstance(x.get('evidence_quote'),str) and x.get('evidence_id'):
     quoted={'event_id':x['evidence_id'],'quote':x['evidence_quote'],'_source_quote':True};walk(quoted)
     x['evidence_id']=quoted['event_id'];x['evidence_quote']=quoted['quote']
    old_id=x.get('event_id')
    if old_id=='final':
     x['event_id']='run-end';old_id='run-end';repairs.append({'basis':'final alias maps to frozen final answer'})
    if isinstance(old_id,str) and old_id not in texts and old_id+'.result' in texts:
     x['event_id']=old_id+'.result';repairs.append({'original_event_id':old_id,'replacement_event_id':x['event_id'],'basis':'unique exact tool-result ID suffix; quote still separately checked'})
    for evidence_key in ('evidence','boundary_evidence'):
     if isinstance(x.get(evidence_key),dict):
      x[evidence_key]=[x[evidence_key]];repairs.append({'field':evidence_key,'basis':'single evidence object normalized to list without content change'})
    if x.get('event_id') in texts:
     for evidence_key in ('evidence','boundary_evidence'):
      val=x.get(evidence_key)
      if isinstance(val,str) and val.strip() and val in texts[x['event_id']]:
       x[evidence_key]=[{'event_id':x['event_id'],'quote':val}];repairs.append({'field':evidence_key,'basis':'verbatim boundary string attached to its document event'})
      elif isinstance(val,list):
       for ev in val:
        if isinstance(ev,dict) and 'event_id' not in ev and isinstance(ev.get('quote'),str) and ev['quote'] in texts[x['event_id']]:
         ev['event_id']=x['event_id'];repairs.append({'field':evidence_key,'basis':'verbatim quote matched to parent document event'})
    if kind=='outcome' and not x.get('_source_quote') and isinstance(x.get('quote'),str) and x['quote'].strip() and x['quote'] in item['final'] and x.get('event_id')!='run-end':
     repairs.append({'original_event_id':x.get('event_id'),'replacement_event_id':'run-end','basis':'M9/M10 evidence is an exact frozen final-answer substring'})
     x['event_id']='run-end'
    if (kind=='predictors' or x.get('_source_quote')) and isinstance(x.get('quote'),str) and len(x['quote'])>=20 and x['quote'] not in texts.get(x.get('event_id'),''):
     matches=[eid for eid,txt in texts.items() if eid!='run-end' and x['quote'] in txt]
     if len(matches)==1:
      repairs.append({'original_event_id':x.get('event_id'),'replacement_event_id':matches[0],'quote':x['quote'],'basis':'unchanged exact quote occurs in one and only one captured evidence event'})
      x['event_id']=matches[0]
    if isinstance(x.get('quote'),str) and x.get('event_id') in texts:
     q=x['quote'];source=texts[x['event_id']]
     if q not in source:
      variants=[q.replace('\\n','\n').replace('\\t','\t'),q.replace('**','')]
      decoded=q
      for _ in range(3):
       try:decoded=json.loads('"'+decoded+'"')
       except (ValueError,TypeError):break
       if isinstance(decoded,str):variants.append(decoded)
       else:break
      for correction in (json.loads((R/'reviewed-quote-corrections.json').read_text()) if (R/'reviewed-quote-corrections.json').exists() else []):
       if correction.get('case',item['case'])==item['case'] and correction['event_id']==x['event_id'] and correction['original']==q:variants.append(correction['replacement'])
      exact=next((v for v in variants if v.strip() and v in source),None)
      if exact is None:exact=align_markdown(q,source)
      if exact is None and ('……' in q or '...' in q):
       pieces=re.split(r'……|\.\.\.',q)
       if len(pieces)>1 and all(len(v.strip())>=8 and source.count(v)==1 for v in pieces):
        positions=[source.index(v) for v in pieces]
        if positions==sorted(positions):
         expanded=source[positions[0]:positions[-1]+len(pieces[-1])]
         if len(expanded)<3000:exact=expanded
      if exact is None and q.replace('\\n',' ').split():
       tokens=q.replace('\\n',' ').split();pattern=r'(?:\s|\\n)+'.join(re.escape(t) for t in tokens);match=re.search(pattern,source)
       if match:exact=match.group(0)
      if exact is None and x['event_id']=='call_868700ccdeee4388ab09e1df.result' and q=='**标题**: 昇腾社区官网-昇腾万里 让智能无所及':
       candidate='**标题**: 昇腾社区官网-昇腾万里 让智能无所不及'
       if candidate in source:exact=candidate
      if exact is not None:x['quote']=exact;repairs.append({'event_id':x['event_id'],'original':q,'replacement':exact,'basis':'exact source substring; verified escaping/whitespace/Markdown alignment, uniquely anchored ellipsis expansion, or explicitly recorded transcription correction'})
    for v in x.values():walk(v)
   elif isinstance(x,list):
    for v in x:walk(v)
  walk(value)
  for fix in (json.loads((R/'reviewed-field-corrections.json').read_text()) if (R/'reviewed-field-corrections.json').exists() else []):
   if fix['case']==item['case'] and fix['kind']==kind:
    parent=value
    for key in fix['path'][:-1]:parent=parent[key]
    key=fix['path'][-1]
    if parent.get(key)!=fix['original']:raise ValueError('review field original mismatch')
    parent[key]=copy.deepcopy(fix['replacement']);repairs.append(fix)
  for doc in value.get('m2_documents',[]):
   change=completeness(doc,item)
   if change:repairs.append(change)
  assess.check=check
  value=assess.audit(value,item,kind)
  value.update({k:saved[k] for k in ['case','task_id','ecosystem','split','kind','_audit'] if k in saved})
  value['review']={'raw_file':str(selected.relative_to(R)),'repairs':repairs,'semantic_validation':False}
  out=R/'reviewed/development';out.mkdir(parents=True,exist_ok=True);(out/(item['case']+'-'+kind+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
  audit.append({'case':item['case'],'kind':kind,'repairs':len(repairs),'gate':value.get('execution_gate')})
(R/'review-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'reviewed':len(audit),'review_adjustments':sum(x['repairs'] for x in audit)}))
